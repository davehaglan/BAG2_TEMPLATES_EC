# -*- coding: utf-8 -*-
########################################################################################################################
#
# Copyright (c) 2014, Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################################################################


"""This package defines various passives template classes.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# noinspection PyUnresolvedReferences,PyCompatibility
from builtins import *

from typing import Dict, Set, Any

from bag.layout.routing import TrackID
from bag.layout.template import TemplateBase, TemplateDB

from ..resistor.core import ResArrayBase
from ..analog_core import SubstrateContact, AnalogBase, AnalogBaseInfo


class LoadResistor(ResArrayBase):
    """bias resistor for differential high pass filter.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
            the template database.
    lib_name : str
        the layout library name.
    params : dict[str, any]
        the parameter values.
    used_names : set[str]
        a set of already used cell names.
    **kwargs :
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **Any) -> None
        super(LoadResistor, self).__init__(temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        """Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : Dict[str, Any]
            dictionary of default parameter values.
        """
        return dict(
            res_type='reference',
            em_specs={},
        )

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            l='unit resistor length, in meters.',
            w='unit resistor width, in meters.',
            nx='number of columns.',
            ndum='number of dummies.',
            sub_type='the substrate type.',
            threshold='the substrate threshold flavor.',
            res_type='the resistor type.',
            em_specs='EM specifications for the termination network.',
            show_pins='True to show pins.',
        )

    def _export_to_vm(self, port):
        _, vm_width, xm_width, ym_width = self.w_tracks
        bot_layer = self.bot_layer_id
        warr = port
        for next_layer, next_width in zip(range(bot_layer + 1, bot_layer + 4), self.w_tracks[1:]):
            next_tr = self.grid.coord_to_nearest_track(next_layer, warr.middle, half_track=True)
            tid = TrackID(next_layer, next_tr, width=next_width)
            warr = self.connect_to_tracks(warr, tid, min_len_mode=0)

        return warr

    def draw_layout(self):
        # type: () -> None

        kwargs = self.params.copy()
        nx = kwargs.pop('nx')
        ndum = kwargs.pop('ndum')
        show_pins = kwargs.pop('show_pins')

        # draw array
        self.draw_array(nx=nx + 2 * ndum, ny=1, edge_space=False, grid_type='low_res', **kwargs)

        # for each resistor, bring it to metal 5
        for idx in range(nx + 2 * ndum):
            bot, top = self.get_res_ports(0, idx)
            bot = self._export_to_vm(bot)
            top = self._export_to_vm(top)
            if idx < ndum or idx >= nx + ndum:
                self.add_pin('dummy', self.connect_wires([bot, top]), show=show_pins)
            else:
                self.add_pin('bot<%d>' % (idx - ndum), bot, show=show_pins)
                self.add_pin('top<%d>' % (idx - ndum), top, show=show_pins)


class CMLLoadSingle(TemplateBase):
    """An template for creating high pass filter.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
            the template database.
    lib_name : str
        the layout library name.
    params : dict[str, any]
        the parameter values.
    used_names : set[str]
        a set of already used cell names.
    **kwargs :
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **Any) -> None
        super(CMLLoadSingle, self).__init__(temp_db, lib_name, params, used_names, **kwargs)
        self._tot_width = None
        self._output_tracks = None

    @property
    def output_tracks(self):
        return self._output_tracks

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        """Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : Dict[str, Any]
            dictionary of default parameter values.
        """
        return dict(
            show_pins=True,
        )

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            res_params='load resistor parameters.',
            sub_params='substrate parameters.',
            show_pins='True to draw pin layouts.',
        )

    def draw_layout(self):
        # type: () -> None

        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, res_params, sub_params, show_pins):

        res_params = res_params.copy()
        res_params['show_pins'] = False
        res_master = self.new_template(params=res_params, temp_cls=LoadResistor)
        top_layer, nx_arr, ny_arr = res_master.size

        sub_params = sub_params.copy()
        sub_params['sub_type'] = res_params['sub_type']
        sub_params['threshold'] = res_params['threshold']
        sub_params['top_layer'] = top_layer
        sub_params['blk_width'] = nx_arr
        sub_params['show_pins'] = False

        _, blk_h = self.grid.get_block_size(top_layer)
        sub_master = self.new_template(params=sub_params, temp_cls=SubstrateContact)
        ny_shift = sub_master.size[2]
        res_inst = self.add_instance(res_master, inst_name='XRES')
        top_yo = (ny_arr + ny_shift) * blk_h
        top_inst = self.add_instance(sub_master, inst_name='XTSUB', loc=(0.0, top_yo), orient='MX')

        port_name = sub_master.port_name
        sub_warrs = top_inst.get_all_port_pins(port_name)
        for dum_warr in res_inst.get_all_port_pins('dummy'):
            warr = self.connect_to_tracks(sub_warrs, dum_warr.track_id, track_lower=dum_warr.upper)
            self.add_pin(port_name, warr, show=show_pins)

        self._output_tracks = []
        for idx in range(res_params['nx']):
            top = res_inst.get_all_port_pins('top<%d>' % idx)[0]
            self._output_tracks.append(top.track_id.base_index)
            warr = self.connect_to_tracks(sub_warrs, top.track_id, track_lower=top.upper)
            self.add_pin(port_name, warr, show=show_pins)
            self.reexport(res_inst.get_port('bot<%d>' % idx), net_name='out<%d>' % idx, show=show_pins)

        # recompute array_box/size
        self.size = top_layer, nx_arr, ny_arr + ny_shift
        self.array_box = top_inst.array_box.extend(y=0, unit_mode=True)


class CMLCorePMOS(AnalogBase):
    """A differential NMOS passgate track-and-hold circuit with clock driver.

    This template is mainly used for ADC purposes.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
            the template database.
    lib_name : str
        the layout library name.
    params : dict[str, any]
        the parameter values.
    used_names : set[str]
        a set of already used cell names.
    kwargs : dict[str, any]
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            lch='channel length, in meters.',
            w='pmos width, in meters/number of fins.',
            fg='number of fingers per segment.',
            fg_ref='number of current mirror reference fingers per segment.',
            output_tracks='output track indices on vm layer.',
            em_specs='EM specs per segment.',
            threshold='transistor threshold flavor.',
            input_width='input track width',
            input_space='input track space',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            guard_ring_nf='Guard ring width in number of fingers.  0 for no guard ring.',
            tot_width='Total width in number of source/drain tracks.',
            show_pins='True to draw pins.',
        )

    @classmethod
    def get_default_param_values(cls):
        """Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : dict[str, any]
            dictionary of default parameter values.
        """
        return dict(
            gr_w=None,
            guard_ring_nf=0,
            show_pins=True,
        )

    def draw_layout(self):
        self._draw_layout_helper(**self.params)

    # noinspection PyUnusedLocal
    def _draw_layout_helper(self, lch, w, fg, fg_ref, output_tracks, em_specs, threshold,
                            input_width, input_space, ntap_w, guard_ring_nf, tot_width, show_pins):
        """Draw the layout of a transistor for characterization.
        """
        # get AnalogBaseInfo
        layout_info = AnalogBaseInfo(self.grid, lch, guard_ring_nf)

        # compute total number of fingers to achieve target width.
        res = self.grid.resolution
        tot_width_unit = int(round(tot_width / res))
        sd_pitch = layout_info.sd_pitch_unit
        if tot_width_unit % sd_pitch != 0:
            raise ValueError('total width = %.4g not multiple of source/drain pitch.' % tot_width)

        num_pitch = tot_width_unit // sd_pitch

        fg_tot = num_pitch
        cur_width = layout_info.get_total_width(fg_tot, guard_ring_nf=guard_ring_nf)
        while cur_width > num_pitch:
            fg_tot -= 1
            cur_width = layout_info.get_total_width(fg_tot, guard_ring_nf=guard_ring_nf)

        if cur_width != num_pitch:
            raise ValueError('Cannot achieve a total width of %.4g' % tot_width)

        # find number of tracks needed for output/tail tracks from EM specs
        hm_layer = layout_info.mconn_port_layer + 1
        hm_width = self.grid.get_min_track_width(hm_layer, **em_specs)
        hm_space = self.grid.get_num_space_tracks(hm_layer, hm_width)
        vm_layer = hm_layer + 1
        vm_width = self.grid.get_min_track_width(vm_layer, bot_w=hm_width, **em_specs)

        # find number of tracks needed for current reference from EM specs
        cur_ratio = fg / fg_ref
        num_seg = len(output_tracks)
        ref_em_specs = em_specs.copy()
        for key in ['idc', 'iac_rms', 'iac_peak']:
            if key in ref_em_specs:
                ref_em_specs[key] *= num_seg / cur_ratio
        hm_width_ref = self.grid.get_min_track_width(hm_layer, **ref_em_specs)
        hm_space_ref = self.grid.get_num_space_tracks(hm_layer, hm_width_ref)

        input_space = max(input_space, hm_space_ref, hm_space)

        pw_list = [w, w, w]
        pth_list = [threshold, threshold, threshold]
        pg_tracks = [input_width, input_space + hm_width_ref + hm_space, input_width]
        pds_tracks = [input_space + hm_width, 2 * hm_width + hm_space + input_space, input_space + hm_width]

        # draw transistor rows
        self.draw_base(lch, fg_tot, ntap_w, ntap_w, [],
                       [], pw_list, pth_list, gds_space=0,
                       ng_tracks=[], nds_tracks=[],
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       p_orientations=['MX', 'R0', 'R0'],
                       guard_ring_nf=guard_ring_nf,
                       pgr_w=ntap_w, ngr_w=ntap_w)

        # compute track ids
        outp_tid = self.make_track_id('pch', 2, 'ds', (hm_width - 1) / 2 + input_space, width=hm_width)
        outn_tid = self.make_track_id('pch', 0, 'ds', (hm_width - 1) / 2 + input_space, width=hm_width)
        vdd_tid = self.make_track_id('pch', 1, 'ds', (hm_width - 1) / 2, width=hm_width)
        tail_tid = self.make_track_id('pch', 1, 'ds', (hm_width - 1) / 2 + hm_width + hm_space, width=hm_width)
        inp_tid = self.make_track_id('pch', 0, 'g', (input_width - 1) / 2, width=input_width)
        inn_tid = self.make_track_id('pch', 2, 'g', (input_width - 1) / 2, width=input_width)
        bias_tid = self.make_track_id('pch', 1, 'g', input_space + (hm_width_ref - 1) / 2, width=hm_width_ref)

        # draw transistors and connect
        inp_list = []
        inn_list = []
        tail_list = []
        bias_list = []
        vdd_h_list = []
        outp_list = []
        outn_list = []
        for idx, vm_idx in enumerate(output_tracks):
            # TODO: add check that fg + fg_ref is less than or equal to output pitch?
            vtid = TrackID(vm_layer, vm_idx, width=vm_width)
            # find column index that centers on given track index
            x_coord = self.grid.track_to_coord(vm_layer, vm_idx, unit_mode=True)
            col_center = layout_info.coord_to_col(x_coord, unit_mode=True)
            col_idx = col_center - (fg // 2)
            # draw transistors
            mtop = self.draw_mos_conn('pch', 2, col_idx, fg, 0, 2)
            mmid = self.draw_mos_conn('pch', 1, col_idx, fg, 1, 1)
            mbot = self.draw_mos_conn('pch', 0, col_idx, fg, 2, 0)
            mref = self.draw_mos_conn('pch', 1, col_idx + fg, fg_ref, 1, 1, diode_conn=True)
            # connect
            inp_list.append(mbot['g'])
            inn_list.append(mtop['g'])
            bias_list.extend((mmid['g'], mref['g']))
            tail_list.extend((mtop['s'], mbot['s'], mmid['s']))

            outp_h = self.connect_to_tracks(mtop['d'], outp_tid)
            outp_list.append(outp_h)
            self.add_pin('outp<%d>' % idx, self.connect_to_tracks(outp_h, vtid), show=show_pins)
            outn_h = self.connect_to_tracks(mbot['d'], outn_tid)
            outn_list.append(outn_h)
            self.add_pin('outn<%d>' % idx, self.connect_to_tracks(outn_h, vtid), show=show_pins)

            vdd_h = self.connect_to_tracks(mmid['d'], vdd_tid)
            vdd_h_list.append(vdd_h)
            self.add_pin('VDD<%d>' % idx, self.connect_to_tracks(vdd_h, vtid, min_len_mode=0), show=show_pins)

        self.connect_wires(vdd_h_list)
        self.connect_wires(outp_list)
        self.connect_wires(outn_list)
        self.add_pin('inp', self.connect_to_tracks(inp_list, inp_tid), show=show_pins)
        self.add_pin('inn', self.connect_to_tracks(inn_list, inn_tid), show=show_pins)
        self.connect_to_tracks(tail_list, tail_tid)
        self.add_pin('ibias', self.connect_to_tracks(bias_list, bias_tid), show=show_pins)

        ptap_warrs, ntap_warrs = self.fill_dummy()
        self.add_pin('VSS', ptap_warrs, show=show_pins)
        self.add_pin('VDD', ntap_warrs, show=show_pins)


class CMLDriverPMOS(TemplateBase):
    """An template for creating high pass filter.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
            the template database.
    lib_name : str
        the layout library name.
    params : dict[str, any]
        the parameter values.
    used_names : set[str]
        a set of already used cell names.
    **kwargs :
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        # type: (TemplateDB, str, Dict[str, Any], Set[str], **Any) -> None
        super(CMLDriverPMOS, self).__init__(temp_db, lib_name, params, used_names, **kwargs)
        self._tot_width = None
        self._output_tracks = None

    @property
    def output_tracks(self):
        return self._output_tracks

    @classmethod
    def get_default_param_values(cls):
        # type: () -> Dict[str, Any]
        """Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : Dict[str, Any]
            dictionary of default parameter values.
        """
        return dict(
            show_pins=True,
        )

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            res_params='load resistor parameters.',
            lch='channel length, in meters.',
            w='pmos width, in meters/number of fins.',
            fg='number of fingers per segment.',
            fg_ref='number of current mirror reference fingers per segment.',
            threshold='transistor threshold flavor.',
            input_width='input track width',
            input_space='input track space',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            guard_ring_nf='Guard ring width in number of fingers.  0 for no guard ring.',
            show_pins='True to draw pins.',
        )

    def draw_layout(self):
        # type: () -> None

        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, res_params, lch, w, fg, fg_ref, threshold, input_width,
                            input_space, ntap_w, guard_ring_nf, show_pins):

        sub_params = dict(
            lch=lch,
            w=ntap_w,
        )

        load_params = dict(
            res_params=res_params.copy(),
            sub_params=sub_params,
            show_pins=False,
        )

        load_master = self.new_template(params=load_params, temp_cls=CMLLoadSingle)

        core_params = dict(
            lch=lch,
            w=w,
            fg=fg,
            fg_ref=fg_ref,
            output_tracks=load_master.output_tracks,
            em_specs=res_params['em_specs'].copy(),
            threshold=threshold,
            input_width=input_width,
            input_space=input_space,
            ntap_w=ntap_w,
            guard_ring_nf=guard_ring_nf,
            tot_width=load_master.array_box.width,
            show_pins=False,
        )

        core_master = self.new_template(params=core_params, temp_cls=CMLCorePMOS)

        # place instances
        _, load_height = self.grid.get_size_dimension(load_master.size, unit_mode=True)
        _, core_height = self.grid.get_size_dimension(core_master.size, unit_mode=True)
        loadn = self.add_instance(load_master, 'XLOADN', (0, load_height), orient='MX', unit_mode=True)
        core = self.add_instance(core_master, 'XCORE', (0, load_height), unit_mode=True)
        loadp = self.add_instance(load_master, 'XLOADP', (0, load_height + core_height), unit_mode=True)

        self.array_box = loadn.array_box.merge(loadp.array_box)
        self.set_size_from_array_box(load_master.size[0])

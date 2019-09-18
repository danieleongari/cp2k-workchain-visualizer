""" Utilities for cp2k-workchain-visualizer
"""

ha2u = {'eV': 27.211399}

def get_id_from_user():
    """Get id from user"""
    from bokeh.io import curdoc
    try:
        name = curdoc().session_context.request.arguments.get('id')[0]
        if isinstance(name, bytes):
            wc_id = name.decode()
    except (TypeError, KeyError, AttributeError):
        wc_id = '57a25492-4260-4a17-83c2-30526d67c7b1'

    return wc_id

def node_info_string(wcnode):
    string =  """
    pk: {}
    uuid: {}
    label: {}
    description: {}
    """.format(
        wcnode.pk,
        wcnode.uuid,
        wcnode.label,
        wcnode.description)
    return string

def out_info_string(out_dict, units):
    string =  """
    Cell resized: {},
    Number of atoms: {}
    Final bandgap (Alpha): {:.3f} eV
    Final bandgap (Beta): {:.3f} eV
    Number of stages discarded & valid: {} & {}
    """.format(
        out_dict['cell_resized'],
        out_dict['natoms'],
        out_dict['final_bandgap_spin1_au']*ha2u[units],
        out_dict['final_bandgap_spin2_au']*ha2u[units],
        out_dict['nsettings_discarded'],
        out_dict['nstages_valid'])
    return string

def dict_to_string(dict):
    import yaml
    string = """
```python
{}
```
""".format(yaml.dump(dict, default_flow_style=False, indent=2))
    return string


def structure_jsmol(cif_str):
    """Visualize a CIF string in JSMol """
    from jsmol_bokeh_extension import JSMol
    import bokeh.models as bmd

    script_source = bmd.ColumnDataSource()

    info = dict(
        height="100%",
        width="100%",
        use="HTML5",
        serverURL="https://chemapps.stolaf.edu/jmol/jsmol/php/jsmol.php",
        j2sPath="https://chemapps.stolaf.edu/jmol/jsmol/j2s",
        #serverURL="https://www.materialscloud.org/discover/scripts/external/jsmol/php/jsmol.php",
        #j2sPath="https://www.materialscloud.org/discover/scripts/external/jsmol/j2s",
        #serverURL="detail/static/jsmol/php/jsmol.php",
        #j2sPath="detail/static/jsmol/j2s",
        script="""set antialiasDisplay ON;
    load data "cifstring"
    {}
    end "cifstring"
    """.format(cif_str)
        ## Note: Need PHP server for approach below to work
        #    script="""set antialiasDisplay ON;
        #load cif::{};
        #""".format(get_cif_url(entry.filename))
    )

    applet = JSMol(
        width=600,
        height=600,
        script_source=script_source,
        info=info,
        #js_url="detail/static/jsmol/JSmol.min.js",
    )

    return applet

def plot_steps(out_dict, units):
    """ Plot convergence steps in Bokeh """
    from bokeh.models import BoxAnnotation
    from bokeh.plotting import figure, show, output_notebook
    import bokeh.models as bmd

    tooltips = [
        ("Step (total)", "@index"),
        ("Step (stage)", "@step"),
        ("Energy", "@energy eV/atom"),
        ("Energy (dispersion)", "@dispersion_energy_au Ha"),
        ("SCF converged", "@scf_converged"),
        ("Cell A", "@cell_a_angs Angs"),
        ("Cell Vol", "@cell_vol_angs3 Angs^3"),
        ("MAX Step", "@max_step_au Bohr"),
        ("Pressure", "@pressure_bar bar")
    ]
    hover = bmd.HoverTool(tooltips=tooltips)
    TOOLS = ["pan", "wheel_zoom", "box_zoom", "reset", "save", hover]

    natoms = out_dict['natoms']
    values = [ x/natoms*ha2u[units] for x in out_dict['step_info']['energy_au'] ]
    values = [ x-min(values) for x in values ]

    data = bmd.ColumnDataSource(data=dict( index=range(len(values)),
                                           step=out_dict['step_info']['step'],
                                           energy=values,
                                           dispersion_energy_au=out_dict['step_info']['dispersion_energy_au'],
                                           scf_converged=out_dict['step_info']['scf_converged'],
                                           cell_a_angs=out_dict['step_info']['cell_a_angs'],
                                           cell_vol_angs3=out_dict['step_info']['cell_vol_angs3'],
                                           max_step_au=out_dict['step_info']['max_step_au'],
                                           pressure_bar=out_dict['step_info']['pressure_bar'],
                                           ))

    p = figure(tools=TOOLS, title='Energy profile of the DFT minimization',
            height=350, width=550)

    p.xgrid.grid_line_color=None
    p.xaxis.axis_label = 'Steps'
    p.yaxis.axis_label = 'Energy ({}/atom)'.format(units)

    # Colored background
    colors = ['red','orange','green','yellow','cyan','pink','palegreen']
    start = 0
    for i,steps in enumerate(out_dict['stage_info']['nsteps']):
        end = start+steps
        p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.2, fill_color=colors[i]))
        start = end

    # Trace line and markers
    p.line('index', 'energy', source=data, line_color='blue')
    p.circle('index', 'energy', source=data, line_color='blue', size=3)
    return p

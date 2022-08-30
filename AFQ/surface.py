import neuropythy as ny
# import nilearn as ni

# GOAL: given a subject SUB1 with surface surf1, V vertices,
# and a .trk file
# make a surface-level stat. map of shape (V,), which has
# for each vertex v, a count of how many endpoints are closest to that vertex,
# after eliminating endpoints too far from any vertex.

# Thus, one should be able to visualize the map `endpoint_counts` as a stat map
# on the same subject's cortical surface.

def streamlines_to_endpoints(nysubj, streamlines,
                             streamline_end='both',
                             surface='white',
                             distance_threshold=2,
                             affine=None,
                             output='count'):
    """Converts a list of streamline coordinates into endpoint maps.

    Given a neuropythy subject (either a FreeSurfer or HCP subject) and a list,
    of streamlines, this function converts the streamlines into an endpoint map.
    Endpoint maps are cortical surface properties (i.e., one value per surface
    vertex of each hemisphere), that provide the count of number of streamlines
    that end at each surface vertex.

    Parameters
    ----------
    nysubj : neuropythy Subject
        A `neuropythy.mri.Subject` object, which can be loaded from a FreeSurfer
        directory (see `neuropythy.freesurfer_subject`) or from a Human
        Connectome Project directory (see `neuropythy.hcp_subject`). This is the
        subject for whom the streamlines were collected.
    streamlines : list-like of streamline coordinates
        A list of streamlines. Each streamline must be a numpy array with shape
        `(N, 3)` (the `N` may be different for each streamline). If one loads a
        `.trk` file using the `nibabel.streamlines.load` function, for example
        `trk_data = nibabel.streamlines.load('myfile.trk')`, then the
        `streamlines` member (`trk_data.streamlines`) is in the correct format
        for this parameter.
    streamline_end : 'both' or 'head' or 'tail', optional
        Should the beginnings (`'head'`), the ends (`'tail'`), or both the ends
        and the beginnings (`'both'`, the default) of the streamlines be used to
        create the endpoint maps.
    distance_threshold : positive float, optional
        The maximum distance from a surface vertex that an endpoint may be in
        order to be considered close to that vertex. The default is `2.0`.
    surface : 'white' or 'midgray' or 'pial', optional
        The surface whose vertex coordinates are used to determine whether each
        streamline endpoint terminates in the gray-matter. I.e., a streamline
        endpoint is considered to terminate at a specific vertex if the endpoint
        is closer to that vertex than to any other vertex and the distance from
        the vertex to the endpoint is less than the `max_distance` parameter.
        The default is `'white'`.
    affine : affine-like or None
        An affine transformation to apply to the streamlines prior to the
        calculation. This may be anything that can be converted into an affine
        matrix using the `neuropythy.to_affine` function. The default, `None`,
        applies no affine to the streamlines.
    output : 'count' or 'pdf'
        Whether to output a count of endpoints per vertex or a probability
        density function. The probability density function is calculated by
        dividing the count of streamlines ending at each vertex by the total
        number of streamlines that ended on a vertex. The default is `'count'`.
        Note that for `'pdf'`, the probability density function sums to 1 over
        each hemisphere, not over both hemispheres.

    Returns
    -------
    dict
        A dictionary with the keys `'lh'` and `'rh'`, which contain the left and
        right hemisphere endpoint maps, respectively.
    """
    import numpy as np
    # Sanity check some input arguments.
    if output != 'count' and output != 'pdf':
        raise ValueError("option output must be 'count' or 'pdf'")
    # It's okay to pass the trk data (which holds the streamlines).
    if hasattr(streamlines, 'streamlines'):
        streamlines = streamlines.streamlines
    # Get the heads and tails for the streamlines.
    trk_heads = np.array([sl[0] for sl in streamlines])
    trk_tails = np.array([sl[-1] for sl in streamlines])
    # What are the endpoints we are using?
    if streamline_end == 'head':
        endpoints = trk_heads
    elif streamline_end == 'tail':
        endpoints = trk_tails
    elif streamline_end == 'both':
        endpoints = np.vstack([trk_heads, trk_tails])
    else:
        raise ValueError("streamline_end must be 'head', 'tail', or 'both'")
    # If there's an affine transformation provided, apply it to the endpoints.
    if affine is not None:
        from neuropythy.util import (to_affine, apply_affine)
        affine = to_affine(affine)
        endpoints = apply_affine(affine, endpoints.T).T
    # Grab the vertex spatial hashes and lookup the streamlines;
    # This must be done for each hemisphere.
    endpoint_counts = {}
    for h in ['lh', 'rh']:
        hemi = nysubj.hemis[h]
        surf = hemi.surface(surface)
        spatial_hash = surf.vertex_hash
        # Temporarily store the counts here:
        epcount = np.zeros(hemi.vertex_count, dtype=int)
        # Find the nearest vertices to each endpoint.
        (d, vertex_i) = spatial_hash.query(endpoints)
        # Filter out anything farther than the max distance from the
        # midgray surface.
        i = d < distance_threshold
        vertex_i = vertex_i[i]
        # Now add these up into a single vector.
        vcount = np.bincount(vertex_i)
        epcount[:len(vcount)] = vcount
        if output == 'pdf':
            epcount = epcount / np.sum(epcount)
        endpoint_counts[h] = epcount
    # The endpoint_counts now contain the maps.
    return endpoint_counts

# basic idea of what the freesurfer align function should be:
def freesurfer_align_streamlines(sub, trk):
    import numpy as np, dipy
    # TODO - which dipy function should do this ??
    aff = np.linalg.inv(sub.lh.affine)
    return dipy.apply_affine(aff, trk)



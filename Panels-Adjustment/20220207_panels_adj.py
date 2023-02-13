import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th
import random
import math
from copy import deepcopy



"""
Notes:
----------------------------------------------------
1. Most of the surface are trimmed surfaces, therefore dealing with them yeilds as an output the untrimmed surface
The solution adopted finally is to use the brep off them and try to work with it.

"""
#manually select 2 panels --> ok
#Find intersection and get the actual distance between them 
#extrude (offset value + retreat) and make a box and find intersection panel to box
#retreat the line (side that aligns with this side) 
#make sure tht the connection line is greate than a threshold?

#so we import the extruded panels (4.5 one side + 0.5 second side cm)(input)
#we have one of the 3 options:
#1. split the panel or boolean difference
#2. get the untrimmed surface and offset then trim the panel
#3. scale to a certain limit the cutting panel to cover the required distance

def trim_intersecting_panel_pair(cutting_brep, brep_needed, option_type, trim_type = 2):
    #1. split the panel or boolean difference
    if option_type == 1:
        pass

    if option_type == 2: #transforming the big surface into untrimmed surface
        brep_faces = cutting_brep.Faces
        surfaces = []
        for index in range(brep_faces.Count):
            surfaces.append(brep_faces[index].UnderlyingSurface())
        surfaces.sort(key=lambda surface: surface.GetSurfaceSize()[1] * surface.GetSurfaceSize()[2], reverse=True)
        #Analyising surface 1 and 2:
        srf1 = surfaces[0]
        srf2 = surfaces[1]

        brep1 = srf1.ToBrep()
        brep1_edges = brep1.Edges
        edges_1 = []
        for index in range(brep1_edges.Count):
            edges_1.append(brep1_edges[index].EdgeCurve)
        b1_curve = rg.Curve.JoinCurves(edges_1)[0]
        print(b1_curve)

        brep2 = srf2.ToBrep()
        brep2_edges = brep2.Edges
        edges_2 = []
        for index in range(brep2_edges.Count):
            edges_2.append(brep2_edges[index].EdgeCurve)
        b2_curve = rg.Curve.JoinCurves(edges_2)[0]

        #create the loft from the extracted curves:
        uncapped_cutting_brep = rg.Brep.CreateFromLoft([b1_curve, b2_curve],rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Normal, False)[0]
        cutting_brep = rg.Brep.CapPlanarHoles(uncapped_cutting_brep, 0.001)


    if trim_type == 1:
            breps = brep_needed.Split(cutting_brep, 0.01) 
            
    elif trim_type == 2:
            breps = rg.Brep.CreateBooleanDifference(brep_needed,cutting_brep, 0.01)
    
    #get the brep with the maximum volume: (just an intuition)
    if len(breps) > 0:
        if len(breps) > 1:
            breps.sort(key=lambda brep: brep.GetVolume(), reverse=True)
        brep_needed = breps[0]  
    else:
        print("there is a problem in the panel") 

    #modify the brep needed to obtain the right geometry
    #1. get the faces:
    brep_faces = brep_needed.Faces
    breps_from_faces = []
    for index in range(brep_faces.Count):
        breps_from_faces.append(brep_faces.ExtractFace(index))  
    breps_from_faces.sort(key=lambda brep: brep.GetArea(), reverse=True)
    brep1 = breps_from_faces[1]
    brep2 = breps_from_faces[0]
  
    print (brep1)
    
    srf1 =  brep1.Surfaces[0]
    srf1.SetDomain(0, rg.Interval(0,1))
    srf1.SetDomain(1, rg.Interval(0,1))

    pt1 = srf1.Evaluate(0.5,0.5,1)[1]
    pt2 = rg.Brep.ClosestPoint(brep2, pt1)
    vector_centers = pt2 - pt1
    curve = rg.LineCurve(pt1, pt2)
    new_brep2 = deepcopy(brep1)
    new_brep2.Translate(vector_centers)

    brep_needed_tampered =  rg.BrepFace.CreateExtrusion(brep1.Faces[0], curve, True)
 

    return cutting_brep, brep_needed_tampered

######################################################################################################################################


cuttingbrep, brep_needed_tampered = trim_intersecting_panel_pair(cutter_brep, brep_needed,option_type,  trim_type)


















#surfaces = th.list_to_tree(surfaces)
#curves = rg.Curve.JoinCurves([curve1, curve2], 0.01)

#!!!try add different options such as brep difference, brep intersection, brep split !!
#if option_selector == 1:
#    lista[0] = 1
#if option_selector == 2:
#    lista[1] = 1222
#Try the intersection between breps and curves
#print(curves)

#rg.Surface.Split()
#rg.Surface.Trim()
#rg.Surface.ClosestPoint()
#goal get u and v!!


  #gets the domain of the surface
    # interval_u = rg.Surface.Domain(surface_dummy,0)
    # interval_v = rg.Surface.Domain(surface_dummy, 1)

    # mid_u = interval_u.Mid
    # mid_v = interval_v.Mid
    # _, point, vectors =  rg.Surface.Evaluate(surface_dummy, mid_u,mid_v, 1)

#New function: 
# takes in a list of all possible panels with their 
"""
Notes:
1. Trying bounding box of the cutting brep doesnt work as it yields a big unrealistic box 
"""
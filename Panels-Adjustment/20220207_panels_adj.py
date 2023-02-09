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

print("a")
#1. Create Brep from the surface (main)
def trim_intersecting_panel_pair(brep1, brep2, total_extrusion, add_tolerance, flip_box):
    #Create Brep of the main surface and for simplicity explode from both sides
    brep_raw = deepcopy(brep1)

    #rg.Surface.Offset
    #Solution no. 1:
    #Step 1: Create a dummy box for cutting
    if flip_box:
        brep_raw.Flip()
    brep_trim_boxes,_,_ = rg.Brep.CreateOffsetBrep(brep_raw,total_extrusion + add_tolerance, True, True, 0.01)

    #Step 2: Cut the layer in the box
    breps = rg.Brep.Split(brep_trim_boxes[0], brep2, 0.01)
    print (breps)
   
   
   
    #Solution no.2: (offset 2 surfaces and join them)
    #surface_dummy_flipped = surface_dummy.Reverse(0)
    #surface_dummy_flipped.Reverse(1, True)
    
    #offset_surf_a = rg.Surface.Offset(surface_dummy,total_extrusion + add_tolerance, 0.01)
    #offset_surf_b = rg.Surface.Offset(surface_dummy_flipped,total_extrusion + add_tolerance, 0.01)

    return brep_trim_boxes[0], breps



brep, breps =  trim_intersecting_panel_pair(brep1, brep2, 20,1, False)
breps = th.list_to_tree(breps)
#surfaces = th.list_to_tree(surfaces)
#curves = rg.Curve.JoinCurves([curve1, curve2], 0.01)





#Try the intersection between breps and curves
print(curves)

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

    # normal_vect_surf = rg.Vector3d.CrossProduct(vectors[0],vectors[1])

    
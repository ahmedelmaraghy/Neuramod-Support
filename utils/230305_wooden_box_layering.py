import Rhino.Geometry as rg
from ghpythonlib.treehelpers import list_to_tree as tree
import scriptcontext as sc
import Rhino.DocObjects as rd
import Rhino.DocObjects.ObjectAttributes as obj_att
from Rhino.RhinoDoc import ActiveDoc as doc
from Grasshopper.Kernel.GH_Convert import ToGUID as guid
import System
import Rhino
from System import Array
import rhinoscriptsyntax as rs
import random as r



from Rhino.Geometry import * #for text

def GetObjectLayer(x):
    obj = doc.Objects.Find(x)
    index = obj.Attributes.LayerIndex
    layer = doc.Layers[index]
    return layer.Name


def bake_object(obj,lay,parent_layer_name, col = 25):
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    if obj is not None:
        attr = Rhino.DocObjects.ObjectAttributes()
    
    # Get the index of the layer you want to retrieve
    parent_index = sc.doc.Layers.Find(parent_layer_name, True)
    # Get the name of the layer
    parent_layer =  sc.doc.Layers[parent_index]
    
    sub_parent_index = sc.doc.Layers.Find("{0}_walls".format(parent_layer_name), True)
    if sub_parent_index < 0:
        sub_parent_layer = rd.Layer()
        sub_parent_layer.ParentLayerId = parent_layer.Id
        sub_parent_layer.Name = "{0}_walls".format(parent_layer_name)
        sub_parent_index = sc.doc.Layers.Add(sub_parent_layer)

    parent_layer = sc.doc.Layers[sub_parent_index]

    #Create Child layer
    if lay is not None: # setting layer
        if rd.Layer.IsValidName(lay):           
            index = sc.doc.Layers.Find(lay, True)
            #if index < 0: # if the layer doesn't exist
            print("here")
            child_layer = rd.Layer()
            child_layer.ParentLayerId = parent_layer.Id
            child_layer.Name = lay
            child_layer.Color = System.Drawing.Color.FromArgb(255,r.randint(0,255),0,r.randint(0,255))
            index = sc.doc.Layers.Add(child_layer)
            attr.LayerIndex = index

    if( sc.doc.Objects.AddBrep(obj, attr) != System.Guid.Empty ):
        rc = Rhino.Commands.Result.Success
        sc.doc.Views.Redraw()


def assign_box_names_to_box_faces(list_box_faces,box_centroid, parent_layer_name):
    #list of box tags to be used
    box_TAGS = []
    #tags:['TO','BO','LF','RI','BA','IT','IB','IL','IR']
    # create a vector from the zero zero to the center point of the box
    ref_vec = rg.Point3d(0,0,0) - box_centroid
    ref_vec.Unitize()
    #sort the faces based on area 
    list_box_faces.sort(key = lambda e :(e.ToBrep()).GetArea, reverse=True)
    for index, face in enumerate(list_box_faces):
        layer_name = ""
        #reparametrize surface
        face.SetDomain(0, rg.Interval(0,1))
        face.SetDomain(1, rg.Interval(0,1))
        #get normal at midpoint
        norm_face = rg.Surface.NormalAt(face, 0.5,0.5)

        if index < 5: #the big faces
            if abs(norm_face * ref_vec) > 0.95: #back
                layer_name = 'BA'
            elif norm_face * rg.Vector3d.XAxis > 0.95: #right
                layer_name = 'RI'
            elif norm_face * rg.Vector3d.XAxis < -0.95: #left
                layer_name = 'LF'
            elif norm_face * rg.Vector3d.ZAxis > 0.95: #top
                layer_name = 'TO'
            else:
                layer_name = 'BO'

        else:
            if norm_face.Z < 0.0001 and norm_face.Z > -0.0001:
                if norm_face * rg.Vector3d.XAxis > 0: #hardcoded , all we need is that its +ve num
                    layer_name = 'IR'
                else:
                    layer_name = 'IL'
            else:
                if norm_face * rg.Vector3d.ZAxis > 0: #positive
                    layer_name = 'IT'
                else:
                    layer_name = 'IB'
               

        brep = face.ToBrep()   
        print(face.ToBrep())
        bake_object(brep,layer_name, parent_layer_name)
               

print(parent_layer_name)
if bake:
    assign_box_names_to_box_faces(faces, cp_box, parent_layer_name)
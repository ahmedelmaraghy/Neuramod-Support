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
    
    sub_parent_index = sc.doc.Layers.Find("{0}_panels".format(parent_layer_name), True)
    if sub_parent_index < 0:
        sub_parent_layer = rd.Layer()
        sub_parent_layer.ParentLayerId = parent_layer.Id
        sub_parent_layer.Name = "{0}_panels".format(parent_layer_name)
        sub_parent_index = sc.doc.Layers.Add(sub_parent_layer)


    parent_layer = sc.doc.Layers[sub_parent_index]

    #Create Child layer
    if lay is not None: # setting layer
        if rd.Layer.IsValidName(lay):                   
            #print("here")
            child_layer = rd.Layer()
            child_layer.ParentLayerId = parent_layer.Id
            child_layer.Name = lay
            child_layer.Color = System.Drawing.Color.FromArgb(255,r.randint(0,255),0,r.randint(0,255))
            index = sc.doc.Layers.Add(child_layer)
            attr.LayerIndex = index

    if( sc.doc.Objects.AddBrep(obj, attr) != System.Guid.Empty ):
        rc = Rhino.Commands.Result.Success
        sc.doc.Views.Redraw()

#for each face surface, scale the surface a bit and move the deignated distance
#cut all panels and readd them to the same group based on index. 
#back them again as the correct panels in the right way
def move_surface_and_scale(face, move_value = 0.5, scale_val = 2):
    """
    Translates and scales the surface that will be ised to split the breps
    """
    face.SetDomain(0, rg.Interval(0,1))
    face.SetDomain(1, rg.Interval(0,1))
    normal_vec = face.NormalAt(0.5,0.5)
    #scale the surface to ensure proper cut
    # face.Extend(0, rg.Interval(0-move_value, 1+ move_value))
    # face.Extend(1, rg.Interval(0-move_value, 1+ move_value))
    scale_transform = rg.Transform.Scale(face.PointAt(0.5,0.5), scale_val)
    istransormed = face.Transform(scale_transform)
    #print(face)
    #move the surface 
    translation_vector = normal_vec * move_value * -1
    isTranslated = face.Translate(translation_vector)

    return face

def split_brep_by_face(face, brep):
    #split the brep with box face
    print("brep is {0}".format(brep))
    print("face is {0}".format(face))
    split_breps = brep.Split(face.ToBrep(), 0.001)
    print(split_breps.Count)
    if split_breps.Count > 0:      
        final_breps = []
        for brep in split_breps:
            new_brep = rg.Brep.CapPlanarHoles(brep, 0.001)
            final_breps.append(new_brep)
        final_breps.sort(key = lambda brep: brep.GetVolume())
        return final_breps[-1]
    else:
        return brep
        
    

def split_panels_by_box_faces(box_faces, panels, move_value = 0.5, scale_val = 2):
    """Takes all the panels and iterate for each wooden face if any can split the panel 
    and returns the new panel
    """  
    for face in box_faces:
        #adjust the cutting surface
        new_face = move_surface_and_scale(face,move_value, scale_val)
        #iterate over surfaces:
        for index in range(len(panels)):
            trimmed_panel = split_brep_by_face(new_face, panels[index])
            if trimmed_panel is not panels[index]:
                panels[index] = trimmed_panel

    return panels    


all_panels = split_panels_by_box_faces(faces, panels,move_value, scale_val)
all_panels_layer_names = []

#create new layer names
for id in ids:
    new_name = None
    #print(GetObjectLayer(id))
    layer_name = GetObjectLayer(id)

    if len(layer_name) < 2:
        new_name = "0{0}".format(layer_name)
    else:
        new_name = "{0}".format(layer_name)
    all_panels_layer_names.append(new_name)   

#bake the new layers
if bake:
    for panel, layer_name in zip(all_panels, all_panels_layer_names):
        bake_object(panel,layer_name, parent_layer_name)

import Rhino.Geometry as rg
from ghpythonlib.treehelpers import list_to_tree as tree
import scriptcontext as sc
import Rhino.DocObjects as rd
import Rhino.DocObjects.ObjectAttributes as obj_att
from Rhino.RhinoDoc import ActiveDoc as doc
from Grasshopper.Kernel.GH_Convert import ToGUID as guid
import System.Collections.Generic.IEnumerable as IEnumerable
import System
import Rhino
from System import Array
from ghpythonlib.components import FilletEdge
import random as r
import copy 

import rhinoscriptsyntax as rs
from Grasshopper.Kernel.GH_Convert import ToGHBrep as tobrep

from Rhino.Geometry import * #for text

def GetObjectLayer(x):
    obj = doc.Objects.Find(x)
    index = obj.Attributes.LayerIndex
    layer = doc.Layers[index]
    return layer.Name

def bake_object(obj,lay,col = 25):
    if obj is not None:
        attr = Rhino.DocObjects.ObjectAttributes()
        
    if lay is not None: # setting layer
        if rd.Layer.IsValidName(lay):
            layerIndex = sc.doc.Layers.Find(lay, True)
            if layerIndex < 0: # if the layer doesn't exist
                layer = rd.Layer()
                layer.Name = lay
                layer.Color = System.Drawing.Color.FromArgb(255,r.randint(0,255),0,r.randint(0,255))
                layerIndex = sc.doc.Layers.Add(layer)
            attr.LayerIndex = layerIndex
            displayColor = Rhino.Display.ColorRGBA(layerIndex)
            sc.doc.Objects.AddBrep(obj, attr)

def bake_object_v2(obj,lay,parent_layer_name, col = 25):
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    if obj is not None:
        attr = Rhino.DocObjects.ObjectAttributes()
    
    # Get the index of the layer you want to retrieve
    parent_index = sc.doc.Layers.Find(parent_layer_name, True)
    # Get the name of the layer
    parent_layer =  sc.doc.Layers[parent_index]
    
    sub_parent_index = sc.doc.Layers.Find("{0}_panels_fabri_ready_v2".format(parent_layer_name), True)
    if sub_parent_index < 0:
        sub_parent_layer = rd.Layer()
        sub_parent_layer.ParentLayerId = parent_layer.Id
        sub_parent_layer.Name = "{0}_panels_fabri_ready_v2".format(parent_layer_name)
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

def remove_duplicate_lines_from_polycurve(polycurve, tolerance):
    """Removes the duplicates of intersection lines that may occur when intersecting the 2 breps
    """
    #print("we are here")
    # create a list to store the unique lines
    lines = []
    #print(polycurve.Explode())
    for curve in polycurve.Explode():
        #print("curve is linear : {0}".format(curve.IsLinear()))
        if curve.GetLength() > 20:
            curve.Domain = rg.Interval(0,1)
            lines.append(curve)

    if len(lines) == 1: #only one existing line
        return lines
    else:
        duplicate_lines = []
        unique_lines = []
        
        for i, uni_l in enumerate(lines):
            #print (type(uni_l))
            for j, line in enumerate(lines[i+1:]):
                #check if we can get line out of it:         
                # iterate over the input lines
                #if distance is less than tolerance and direction is same or opposite
                #and the length almost equal then skip and print duplicate line
                len_uni_l = uni_l.GetLength()
                len_line = line.GetLength()
                dir_uni_l = uni_l.TangentAt(0.5)
                dir_line = line.TangentAt(0.5)
                #dir_uni_l.Unitize()
                #dir_line.Unitize()
                distance = uni_l.PointAt(0.5).DistanceTo(line.PointAt(0.5))
                #print("distance is {0}".format(distance))
                #print(rg.NurbsCurve.IsDuplicate(uni_l, line, True, tolerance))
                if (len_uni_l / len_line > 0.90 and len_uni_l / len_line < 1.1) and abs(dir_line * dir_uni_l) > 0.95 and distance < tolerance:
                #if rg.NurbsCurve.IsDuplicate(uni_l, line, True, tolerance):
                    #print("lines are too close")
                    duplicate_lines.append(line)

                
        for uni_l in lines:
            if uni_l not in duplicate_lines:
                unique_lines.append(uni_l) 

        return unique_lines
    
def remove_duplicate_lines(lines, tolerance):
    """Removes the duplicates of intersection lines that may occur when intersecting the 2 breps
    """
    # create a list to store the unique lines
    duplicate_lines = []
    unique_lines = []
    
    for line in lines:
        line.Domain = rg.Interval(0,1)

    for i, uni_l in enumerate(lines):
        for j, line in enumerate(lines[i+1:]):
            #check if we can get line out of it:         
            # iterate over the input lines
            #if distance is less than tolerance and direction is same or opposite
            #and the length almost equal then skip and print duplicate line
            len_uni_l = uni_l.GetLength()
            len_line = line.GetLength()
            dir_uni_l = uni_l.TangentAt(0.5)
            dir_line = line.TangentAt(0.5)
            distance = uni_l.PointAt(0.5).DistanceTo(line.PointAt(0.5))

            if (len_uni_l / len_line > 0.90 and len_uni_l / len_line < 1.1) and abs(dir_line * dir_uni_l) > 0.95 and distance < tolerance:
                #print("lines are too close")
                duplicate_lines.append(line)
            
    for uni_l in lines:
        if uni_l not in duplicate_lines:
            unique_lines.append(uni_l) 

    return unique_lines

def select_small_edge_and_adjust_both_edges(edge_curves, big_edge, edge_extention = 20):
    joined_crvs_list = []
    for curve in edge_curves:
        if curve is not big_edge:
           joined_crvs_list.append(curve)

    curves = rg.Curve.JoinCurves(joined_crvs_list) 
    #print(curves)
    small_edge = None
    long_gov_edge = joined_crvs_list[-1] #longest
    if curves.Count == 1:
       edges = curves[0].DuplicateSegments()
       small_edge = edges[2]

    else: 
        print("we have a problem, inconsistent curve shape")

    #ajust direction of small_edge and make it a line:
    pt_end = small_edge.PointAtEnd
    pt_st = small_edge.PointAtStart
    pt_st_big =  big_edge.PointAt(big_edge.ClosestPoint(pt_st)[1])
    pt_end_big =  big_edge.PointAt(big_edge.ClosestPoint(pt_end)[1])
    small_edge = (rg.Line(pt_st, pt_end)) if pt_st.DistanceTo(pt_st_big) < pt_end.DistanceTo(pt_end_big) else (rg.Line(pt_end, pt_st))
    #extend small edge by a generous value
    small_edge.Extend(edge_extention, 0)
    #find intersection point     
    Point0 = rg.Intersect.Intersection.CurveCurve(small_edge.ToNurbsCurve(),big_edge, 0.001, 0.001)[0].PointA
    #readjust small_edge:
    small_edge = rg.Line(Point0, small_edge.To)
    #use the long gove edge and extend it and get the intersection point with big edge
    long_gov_edge = rg.Line(long_gov_edge.PointAtStart, long_gov_edge.PointAtEnd)
    long_gov_edge.Extend(edge_extention, edge_extention)
    PointX = rg.Intersect.Intersection.CurveCurve(long_gov_edge.ToNurbsCurve(),big_edge, 0.001, 0.001)[0].PointA
    #get the vector and compare with the other vector
    vect = PointX - Point0
    vect.Unitize()
    tes_vect = big_edge.PointAtStart - Point0
    tes_vect.Unitize()
    big_edge = (rg.Line(Point0, big_edge.PointAtStart)) if vect * tes_vect < 0 else (rg.Line(Point0, big_edge.PointAtEnd)) 

    p0 = Point0
    p1 = small_edge.To
    pp0 = Point0
    pp1 = big_edge.To


    return small_edge.ToNurbsCurve(), big_edge.ToNurbsCurve(), p0, p1, pp0, pp1, long_gov_edge

def select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, edge_extention):
    
    p0 = small_edge.PointAtStart
    p1 = small_edge.PointAtEnd
    small_edge_line = rg.Line(p0, p1)
    small_edge_line.Extend(edge_extention, 0)
    pp0 = big_edge.PointAtStart
    pp1 = big_edge.PointAtEnd
    big_edge = rg.Line(pp0, pp1)
    isCut = rg.Intersect.Intersection.LineLine(small_edge_line, big_edge, 0.001, 0.001)[0]
    if not isCut: #we need to reverse the line
        small_edge_line.Extend(-edge_extention, edge_extention)
        small_edge = rg.Line(p1, p0)
    else: 
        small_edge = rg.Line(p0, p1)
    t_big = rg.Intersect.Intersection.LineLine(small_edge_line, big_edge, 0.001, 0.001)[2]
    Point0 = big_edge.PointAt(t_big) 
    vec1 = small_edge.To - small_edge.From
    vec1.Unitize()
    vec2 = big_edge.To - Point0
    vec2.Unitize()
    if vec1 * vec2 < 0:
        big_edge = rg.Line(big_edge.From, big_edge.To)
    else:
        big_edge = rg.Line(big_edge.To, big_edge.From)
    
    return small_edge.ToNurbsCurve(), big_edge.ToNurbsCurve(), small_edge.From, small_edge.To, big_edge.From, big_edge.To
        
def final_adjustment_big_edge(small_edge, big_edge, edge_extention = 200):
    """
    retrims the big edge to take the right curve as there was discreoancy in this part
    """
    #extend small edge by a generous value
    p0 = small_edge.PointAtStart
    p1 = small_edge.PointAtEnd
    small_edge = rg.Line(p0, p1)
    small_edge.Extend(edge_extention, 0)
    #curve = small_edge.ToNurbsCurve()
    pp0 = big_edge.PointAtStart
    pp1 = big_edge.PointAtEnd
    big_edge = rg.Line(pp0, pp1)
    big_edge.Extend(0, 0)

    #find intersection point 
    #print(rg.Intersect.Intersection.LineLine(small_edge, big_edge, 0.001, 0.001)[0])
    #Point0 = rg.Intersect.Intersection.CurveCurve(curve, big_edge.ToNurbsCurve(), 3, 3)[0].PointA
    t_pt =rg.Intersect.Intersection.LineLine(small_edge, big_edge, 0.001, 0.001)[2]
    Point0 = big_edge.PointAt(t_pt) 
    #print(t_pt)
    #readjust small_edge:
    big_edge = rg.Line(Point0, big_edge.To)

    return big_edge.ToNurbsCurve(), big_edge.From, big_edge.To

def add_planes_for_text(p0, p1, pp0, pp1, move_text_distance1, move_text_distance2):
    """takes the points of the small and big line, creates planes for text insertion
    and moves it above of the brackets by a variable distance as preferred
    """
    small_Y = p1 - p0
    small_Y.Unitize()
    big_Y = pp1 - pp0
    big_Y.Unitize()

    small_X = rg.Vector3d.CrossProduct(small_Y, big_Y)
    big_X = rg.Vector3d.CrossProduct(big_Y, small_Y)

    small_origin = p1 + small_Y * move_text_distance1
    big_origin = pp1 + big_Y * move_text_distance2
    #create planes for both tags
    small_plane = rg.Plane(small_origin, small_X, small_Y)
    big_plane = rg.Plane(big_origin, big_X, big_Y)
    
    return [small_plane, big_plane], small_plane.Origin, big_plane.Origin

def add_planes_for_textv2(p0, p1, pp0, pp1, offset, move_text_distance1, move_text_distance2):
    """takes the points of the small and big line, creates planes for text insertion
    and moves it above of the brackets by a variable distance as preferred
    """
    small_Y = p1 - p0
    small_Y.Unitize()
    big_Y = pp1 - pp0
    big_Y.Unitize()

    small_X = rg.Vector3d.CrossProduct(small_Y, big_Y)
    big_X = rg.Vector3d.CrossProduct(big_Y, small_Y)

    small_origin = p1 + small_Y * move_text_distance1
    big_origin = pp1 + big_Y * move_text_distance2
    #create planes for both tags
    small_plane = rg.Plane(small_origin, small_X, small_Y)
    small_plane.Translate(small_plane.Normal * offset)
    big_plane = rg.Plane(big_origin, big_X, big_Y)
    
    return [small_plane, big_plane], small_plane.Origin, big_plane.Origin


def divide_curve_manually(crv, params):
    pts = []
    for param in params:
       pts.append(crv.PointAt(param))
    return pts


  

class Panel_Extrusions(object):
    def __init__(self,intersections):
        self.intersections = intersections
        self.panels = []
        self.panels_ids = []

    def populate_brackets_extrusion(self):
        """iterates over all panels and checks if they are in the list or not, if yes, 
        then perform 
        """
        dibond_panels = []
        for inter in intersections:
        #iterate over all intersections checking if this layer id is in the panels list
        #if yes then remove the brackets and replace the item in the panel with the id index
        #if not then add it first then do the intersection extrusion thing
            for index, panel_id in enumerate(inter.layer.Split('-')):
                if panel_id not in self.panels_ids:
                    self.panels_ids.append(panel_id)
                    self.panels.append(inter.breps[index])

                if panel_id not in B_TAGS:  #to avoid reduction of the brackets from the box walls as till now they are surfaces only !!            
                    new_brep = inter.remove_brackets_from_panel(self.panels[self.panels_ids.index(panel_id)])
                    #replace the new trimmed panel in place of the one before operation
                    self.panels[self.panels_ids.index(panel_id)] = new_brep
                    dibond_panels.append(new_brep)

        return dibond_panels
    

class Intersection(object):
    """Determines all data of intersection between layer and another layer 
        which means between one brep and another brep. 
        crvs: intersection lines
        Layer: name of the 2 layers in rhino string
        breps: actual breps list 
        layers: actual layers list         
    """
    def __init__(self,crvs,layer,breps):
        self.crvs = crvs
        self.layer = layer
        self.breps = breps
        self.box_brep = None
        self.box_normal = None #!! might be inverted !! so is not reliable 
        self.screws = []
        self.text_planes = []
        self.text_planes_brkts = []
        self.tags = []
        self.brackets = []
        self.br_type = []
        self.fab_brackets = []
        self.label1 = TextEntity()
        self.label2 = TextEntity()

        self.hexholders = []

    def remove_brackets_from_panel(self, brep):
        """
        produces the final panel where the brackets are split from the panel, producing the final trimmed panel only from one side of brackets
        """
        original_brep = brep
        
        for bracket in self.brackets: 
            if((rg.Brep.CreateBooleanDifference(original_brep, bracket, 0.001)).Count> 0):
                original_brep = rg.Brep.CreateBooleanDifference(original_brep, bracket, 0.001)[0]
            

        return original_brep
    
    def determining_box_brep(self, B_TAGS):
        box_side_brep = self.breps[0]
        print(self.breps[0].GetVolume())  
        #checks small edge belongs to whom and big edge belongs to whom
        if inter.layer.Split('-')[1] in B_TAGS: #then the sec brep is the brep 
            box_side_brep = self.breps[1]
        #check which is the small side and which is the big_edge (this is kinda redundant but why not extra caution)
        self.box_brep = box_side_brep 
        #steps: 0. sort the sides of the brep box and get the biggest surface 1. get the unitised vec. small edge, 2. unitized vec. big edge and check the dot product
        brep_faces =  box_side_brep.Faces
        breps_from_faces = []
        area_max = float('-inf')
        req_face = box_side_brep.Faces[0]
        for face in brep_faces:
            if face.ToBrep().GetArea() > area_max:
                area_max = face.ToBrep().GetArea()
                req_face = face
        
            print(face.ToBrep().GetArea())

        req_face.SetDomain(0, rg.Interval(0,1))
        req_face.SetDomain(1, rg.Interval(0,1))

        vector = req_face.NormalAt(0.5,0.5)
        self.box_normal = vector

    def adjust_small_big_edge_for_fab_tolerance(self, small_edge, big_edge, p0, p1, pp0, pp1, bracket_tol = 0.15):
        #Untize and check conformity with small edge 
        vec_small = p1 - p0
        vec_big = pp1 - pp0
        vec_small.Unitize()
        vec_big.Unitize()
        p1_t = small_edge.PointAtEnd - vec_small *  bracket_tol 
        pp1_t = big_edge.PointAtEnd - vec_big *  bracket_tol 

        small_edge_tol  = rg.Line(p0, p1_t)
        big_edge_tol = rg.Line(pp0, pp1_t)
        return small_edge_tol.ToNurbsCurve(), big_edge_tol.ToNurbsCurve(), p0, p1_t, pp0, pp1_t

    def adjustment_box_bracket(self, small_edge, big_edge, p0, p1, pp0, pp1, moving_distance = 3.2, edge_extention = 30):
        #Untize and check conformity with small edge 
        right_edge = big_edge
        other_edge = small_edge
        vec1 = pp1 - pp0
        vec2 = p1 - p0
        st_pt = pp0
        end_pt = pp1    
           
        result = vec1 * self.box_normal
        print(result) 
        if not (result <= 0.01 and result >= -0.01):
            print("we are here!!")
            right_edge = small_edge
            other_edge = big_edge
            vec1 = p1 - p0
            vec2 = pp1 - pp0

        vec1.Unitize()
        vec2.Unitize()
        #get the right direction vector for extrusion
        first_cross = rg.Vector3d.CrossProduct(vec1, vec2)
        depth_vector = rg.Vector3d.CrossProduct(vec1, first_cross)
        depth_vector.Unitize()

        #move the right edge to the right quantity
        right_edge.Translate(depth_vector * moving_distance)
        small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(other_edge, right_edge, edge_extention)
        return small_edge, big_edge, p0, p1, pp0, pp1, depth_vector



    def create_screws_holes(self, bracket, depth_vector, dist_screw = 6, dist_head = 3, tolerance = 0.1, rad_screw = 3, rad_head = 6):
        """
        creates the two body for the screw and the screw head 
        """  
        #sort faces and get the midpoint of the face that is in line iwht the decpth vector 
        brep_faces = bracket.Faces
        face_req = bracket.Faces[0]
        area = float('-inf')
        for face in brep_faces:
            face.SetDomain(0, rg.Interval(0,1))
            face.SetDomain(1, rg.Interval(0,1))

            vector = face.NormalAt(0.5,0.5)
            dot_product = vector * depth_vector
            if dot_product < -0.99 : #opposite in direction of the depth_vector
                new_area = face.ToBrep().GetArea()
                if new_area > area:
                    face_req = face
                    area = new_area
                    center_pt = face.PointAt(0.5,0.5)
                
        

        st_pt = face_req.PointAt(0.5,0.5)
        #move the starting point a bit in case of boolean problems
        st_pt_tol = st_pt + depth_vector * -tolerance #in opposite direction
        #create base plane
        base_screw_plane = rg.Plane(st_pt_tol, depth_vector)
        cylinder1 = rg.Cylinder(rg.Circle(base_screw_plane,rad_screw), dist_screw + tolerance)

        #create the screw head
        #move the starting point a bit in case of boolean problems
        st_pt_tol = st_pt + depth_vector * dist_screw  #in opposite direction
        #create base plane
        head_screw_plane = rg.Plane(st_pt_tol, depth_vector)
        cylinder2 = rg.Cylinder(rg.Circle(head_screw_plane,rad_head ), dist_head + tolerance)

        #create screw:
        screw = rg.Brep.CreateBooleanUnion([cylinder1.ToBrep(True, True), cylinder2.ToBrep(True, True)], 0.001)
        if screw.Count > 1:  
            screw_final = rg.Brep.JoinBreps(screw, 0.001)
            print("we are here !!!!")
            screw = screw_final
        print(screw)
        #self.screws.append(screw)
        return screw[0], face_req, center_pt

    def create_hexholder(self, bracket, depth_vector, dist_cyl = 4.1, tolerance = 0.1, rad_cyl = 5.5, rad_hex = 4.1, edges = 6):
            """
            creates the hex holder on the bracket
            """  
            #sort faces and get the midpoint of the face that is in line with the depth vector 
            brep_faces = bracket.Faces
            face_req = bracket.Faces[0]
            area = float('-inf')
            for face in brep_faces:
                face.SetDomain(0, rg.Interval(0,1))
                face.SetDomain(1, rg.Interval(0,1))

                vector = face.NormalAt(0.5,0.5)
                dot_product = vector * depth_vector
                if dot_product < -0.99 : #opposite in direction of the depth_vector
                    new_area = face.ToBrep().GetArea()
                    if new_area > area:
                        face_req = face
                        area = new_area

            hex_st_pt = face_req.PointAt(0.5,0.5)
            #move the starting point a bit in case of boolean problems
            hex_st_pt_tol = hex_st_pt + depth_vector * -tolerance #in opposite direction

            #create the cylinder
            #move the starting point a bit in case of boolean problems
            hex_st_pt_tol1 = hex_st_pt + depth_vector * (dist_cyl - 8.2) #in opposite direction
            #create base plane
            hex_holder_plane = rg.Plane(hex_st_pt_tol1, depth_vector)
            cylinder3 = rg.Cylinder(rg.Circle(hex_holder_plane, rad_cyl), dist_cyl + tolerance)
            
            #create the hexagon
            temp_circle = rs.AddCircle(hex_holder_plane, rad_hex)
            temp_points = rs.DivideCurve(temp_circle, edges, create_points=False, return_points=True)
            temp_points.append(temp_points[0])
            temp_hex = rs.AddPolyline(temp_points)
            #temp_hex = rs.RotateObject(temp_hex, hex_st_pt_tol1, 15, axis=None, copy=False)
            temp_curve = rs.coercecurve(temp_hex)
            rs.DeleteObject(temp_circle)
            rs.DeleteObject(temp_hex)
            hex = rg.Extrusion.Create(temp_curve, dist_cyl + 20, True)
            
            #create hexholder:
            hexholder = rg.Brep.CreateBooleanDifference(cylinder3.ToBrep(True, True), hex.ToBrep(True), 0.001)[0]
    #        if hexholder.Count > 1:
    #            hexholder_final = rg.Brep.JoinBreps(hexholder, 0.001)
    #            print("we are here !!!! WHAT")
    #            hexholder = hexholder_final
            print(hexholder)
            #self.hexholders.append(hexholder)
            return hexholder, face_req      


#FAB_TOL = 0.15

B_TAGS = ('TO','BO','LF','RI','BA','IT','IB','IL','IR')

inter_radius = 10.0
intersections = []

circles = []
sm_edges = []
big_edges = []
p0s = []
p1s = []
pp0s = []
pp1s = []
planes_ = []
edges_3 = []
top_box_brackets = []
screw_cntr_pts = []
debug_panels = []
bracket_lines_tol = []

#get the intersection curves (line likes) between each brep and the ther other 
for brep0,id0 in zip(breps,ids):
    layer0 = GetObjectLayer(id0) #layer0 is the name of the layer of the baked brep in the actual rhino file
    #print("layer 0 is {0}".format(layer0))
    for brep1,id1 in zip(breps,ids):
        layer1 = GetObjectLayer(id1)
        #print("layer 1 is {0}".format(layer1))
        if (brep0 is not brep1) and (("%s-%s"%(layer0,layer1) not in [int.layer for int in intersections])) and (("%s-%s"%(layer1,layer0) not in [int.layer for int in intersections])) and (layer1 not in B_TAGS or layer0 not in B_TAGS):
            #print ("%s-%s"%(layer0,layer1)),"%s-%s"%(layer1,layer0), [int.layer for int in intersections]
            if((((layer0 == "03" and layer1 == "04") or (layer0 == "04" and layer1 == "03")) and (box_number == 5))
               or (((layer0 == "01" and layer1 == "04") or (layer0 == "04" and layer1 == "01")) and (box_number == 5))):
                print("we CHANGED TOL")
                actual_inter_tol = 1.0
            elif(((layer0 == "06" and layer1 == "10") or (layer0 == "10" and layer1 == "06")) and (box_number == 5)):
                actual_inter_tol = 1.5
            elif(((layer0 == "09" and layer1 == "11") or (layer0 == "11" and layer1 == "09")) and (box_number == 11)):
                actual_inter_tol = 0.95
            elif(((layer0 == "08" and layer1 == "07") or (layer0 == "07" and layer1 == "08")) and (box_number == 11)):
                actual_inter_tol = 1.1
            elif(((layer0 == "09" and layer1 == "04") or (layer0 == "04" and layer1 == "09")) and (box_number == 31)):
                actual_inter_tol = 1.1
            elif(((layer0 == "09" and layer1 == "11") or (layer0 == "11" and layer1 == "09")) and (box_number == 5)):
                actual_inter_tol = 1.1
            elif(((layer0 == "09" and layer1 == "00") or (layer0 == "00" and layer1 == "09")) and (box_number == 4)):
                actual_inter_tol = 1.1
            elif(((layer0 == "09" and layer1 == "06") or (layer0 == "06" and layer1 == "09")) and (box_number == 1)):
                actual_inter_tol = 1.5
            elif(((layer0 == "00" and layer1 == "02") or (layer0 == "02" and layer1 == "00")) and (box_number == 1)):
                actual_inter_tol = 1.5
            elif(((layer0 == "00" and layer1 == "03") or (layer0 == "03" and layer1 == "00")) and (box_number == 11)):
                actual_inter_tol = 1.5
            elif(((layer0 == "07" and layer1 == "01") or (layer0 == "01" and layer1 == "07")) and (box_number == 10)):
                actual_inter_tol = 1.5
            elif(((layer0 == "04" and layer1 == "01") or (layer0 == "01" and layer1 == "04")) and (box_number == 17)):
                actual_inter_tol = 1.5
            elif(((layer0 == "07" and layer1 == "11") or (layer0 == "11" and layer1 == "07")) and (box_number == 26)):
                actual_inter_tol = 1.5
           

            else:
                actual_inter_tol = inter_tol_breps 
            if layer1 in B_TAGS or layer0 in B_TAGS:
                if(((layer0 == "BO" and layer1 == "07") or (layer0 == "07" and layer1 == "BO")) and (box_number == 18)):
                    actual_inter_tol += 0.25
                elif(((layer0 == "TO" and layer1 == "09") or (layer0 == "09" and layer1 == "TO")) and (box_number == 0)):
                    actual_inter_tol += 1.3
                elif(((layer0 == "TO" and layer1 == "05") or (layer0 == "05" and layer1 == "TO")) and (box_number == 0)):
                    actual_inter_tol += 0.6
                elif(((layer0 == "TO" and layer1 == "02") or (layer0 == "02" and layer1 == "TO")) and (box_number == 17)):
                    actual_inter_tol += 0.9
                elif(((layer0 == "IR" and layer1 == "11") or (layer0 == "11" and layer1 == "IR")) and (box_number == 3)):
                    actual_inter_tol += 0.9
                elif(((layer0 == "BO" and layer1 == "01") or (layer0 == "01" and layer1 == "BO")) and (box_number == 18)):
                    actual_inter_tol += 0.9

                else:
                    actual_inter_tol += add_B_tol
            bbx = rg.Intersect.Intersection.BrepBrep(brep0,brep1,actual_inter_tol)
            #print(actual_inter_tol)
            if bbx and len(bbx[1])>0:
                list_intersections = []
                for bx in bbx[1]:
                    
                    if bx.GetLength() > 25:
                        #we need to do somthing to prevent duplicates
                        if bx.IsLinear():
                            list_intersections.append(bx)
                        else:
                            output_line = remove_duplicate_lines_from_polycurve(bx,dup_lines_tol)
                            #print("output lines count is {}")
                            if len(output_line) == 1:
                                list_intersections.append(output_line[0])
                                
                            else:
                                print ("we have a problem !!!")

                    else:
                        pass
                        #print ('small')
                list_intersections = remove_duplicate_lines(list_intersections, dup_lines_tol)
                #circles.append(list_intersections)

                interX = Intersection(list_intersections,"%s-%s"%(layer0,layer1),[brep0,brep1])
                intersections.append(interX)


circs,circs_tol, tags = [],[], []
max_area_threshold_applied = max_area_threshold
min_area_threshold_applied = threshold
p_count_max_applied = pcount_max
#this is a bool targeted for tailor made brackets that cant be divided equally but rather using custom legnths
list_is_provided = False
for inter in intersections:
    print("kharaaa")
    #this function determines the which of the 2 breps is the box_panel and then determines a "guidance" normal vector that might be inverted and not reliable to used as proper normal
    inter.determining_box_brep(B_TAGS)
    bracket_index = 0
    for crv in inter.crvs:
        print("number of curves is {0}".format(inter.crvs))
        #checks if curve is long enough to put more than 1 bracket or can only fit no more than 1 bracket only
        #new!! setting domain to be in between 0 and 1
        crv.Domain = rg.Interval(0,1)
        ts =  crv.DivideByCount(2,True)
        #print("domain is {0} and {1}".format(ts[1], ts[2]))
        point,end = crv.PointAt(ts[1]),crv.PointAt(ts[2])
        if box_number == 04 or box_number == 10: #excception !!!!!!
            distance = 80.0
        if (inter.layer == "03-08" or inter.layer == "08-03") and box_number == 26:
            pts = divide_curve_manually(crv, [0.7])
        elif (inter.layer == "05-IT" or inter.layer == "IT-05") and box_number == 26:
            pts = divide_curve_manually(crv, [0.65,0.85])
        elif (inter.layer == "07-11" or inter.layer == "11-07") and box_number == 26:
            pts = divide_curve_manually(crv, [0.3,0.7])
        
        elif (inter.layer == "IL-11" or inter.layer == "11-IL") and box_number == 31:
            pts = divide_curve_manually(crv, [0.3,0.75])
        elif (inter.layer == "09-04" or inter.layer == "04-09") and box_number == 31:
            pts = divide_curve_manually(crv, [0.7])
        elif (inter.layer == "IL-04" or inter.layer == "04-IL") and box_number == 31:
            pts = divide_curve_manually(crv, [0.73])
        elif (inter.layer == "IR-10" or inter.layer == "10-IR") and box_number == 31:
            pts = divide_curve_manually(crv, [0.23, 0.70])
        elif (inter.layer == "IT-02" or inter.layer == "02-IT") and box_number == 31:
            pts = divide_curve_manually(crv, [0.15, 0.325 ,0.5, 0.8])
        elif (inter.layer == "IL-09" or inter.layer == "09-IL") and box_number == 05:
            pts = divide_curve_manually(crv, [0.25, 0.60, 0.85])
        elif (inter.layer == "IR-10" or inter.layer == "10-IR") and box_number == 05:
            pts = divide_curve_manually(crv, [0.125, 0.35])
        elif (inter.layer == "06-10" or inter.layer == "10-06") and box_number == 05:
            pts = divide_curve_manually(crv, [0.3])
        elif (inter.layer == "03-04" or inter.layer == "04-03") and box_number == 05:
            pts = divide_curve_manually(crv, [0.3, 0.8])
        elif (inter.layer == "11-IL" or inter.layer == "IL-11") and box_number == 17:
            pts = divide_curve_manually(crv, [0.3, 0.7, 0.9])
        elif (inter.layer == "10-05" or inter.layer == "05-10") and box_number == 17:
            pts = divide_curve_manually(crv, [0.5, 0.7, 0.9])
        elif (inter.layer == "10-IT" or inter.layer == "IT-10") and box_number == 17:
            pts = divide_curve_manually(crv, [0.2, 0.5, 0.85])
        elif (inter.layer == "02-TO" or inter.layer == "TO-02") and box_number == 17:
            pts = divide_curve_manually(crv, [0.2, 0.4,0.6, 0.8])
        elif (inter.layer == "00-TO" or inter.layer == "TO-00") and box_number == 03:
            pts = divide_curve_manually(crv, [0.21])
        elif (inter.layer == "11-IR" or inter.layer == "IR-11") and box_number == 03:
            pts = divide_curve_manually(crv, [0.25, 0.45, 0.8])
        elif (inter.layer == "09-05" or inter.layer == "05-09") and box_number == 03:
            pts = divide_curve_manually(crv, [0.7])
        elif (inter.layer == "07-IB" or inter.layer == "IB-07") and box_number == 03:
            pts = divide_curve_manually(crv, [0.14, 0.5, 0.85])
        elif (inter.layer == "04-IB" or inter.layer == "IB-04") and box_number == 04:
            pts = divide_curve_manually(crv, [0.8])
        elif (inter.layer == "04-BO" or inter.layer == "BO-04") and box_number == 04:
            pts = divide_curve_manually(crv, [0.7])
        elif (inter.layer == "02-11" or inter.layer == "11-02") and box_number == 00:
            pts = divide_curve_manually(crv, [0.3,0.7])
        elif (inter.layer == "06-IR" or inter.layer == "IR-06") and box_number == 00:
            pts = divide_curve_manually(crv, [0.3,0.6,0.85])
        elif (inter.layer == "09-05" or inter.layer == "05-09") and box_number == 00:
            pts = divide_curve_manually(crv, [0.2,0.45, 0.7])
        elif (inter.layer == "09-06" or inter.layer == "06-09") and box_number == 01 and crv == inter.crvs[0]:
            pts = divide_curve_manually(crv, [0.3,0.575, 0.85])
        elif (inter.layer == "09-06" or inter.layer == "06-09") and box_number == 01 and crv == inter.crvs[1]:
            pts = divide_curve_manually(crv, [0.38])
        elif (inter.layer == "00-02" or inter.layer == "02-00") and box_number == 01:
            pts = divide_curve_manually(crv, [0.2,0.5, 0.7,0.85])
        elif (inter.layer == "11-IB" or inter.layer == "IB-11") and box_number == 01:
            pts = divide_curve_manually(crv, [0.3,0.7])
        elif (inter.layer == "11-IL" or inter.layer == "IL-11") and box_number == 01:
            pts = divide_curve_manually(crv, [0.25,0.5,0.75])
        elif (inter.layer == "07-IB" or inter.layer == "IB-07") and box_number == 07:
            pts = divide_curve_manually(crv, [0.20,0.5,0.85])
        elif (inter.layer == "06-03" or inter.layer == "03-06") and box_number == 07:
            pts = divide_curve_manually(crv, [0.65])
        elif (inter.layer == "07-IT" or inter.layer == "IT-07") and box_number == 07:
            pts = divide_curve_manually(crv, [0.25,0.85])
        
        elif (inter.layer == "04-05" or inter.layer == "05-04") and box_number == 11 and crv == inter.crvs[0]:  # BOX 11: 3 AND 00 ADD MORE BRACKETS # , 4 AND 5 REMOVE 1 BRACKET,#11 AND 9 ADJUST THE BRACKET# 7 AND 8 ADD 2 OR 3 MORE # 8 AND it ADD 2 MORE
            pts = divide_curve_manually(crv, [])
        elif (inter.layer == "04-05" or inter.layer == "05-04") and box_number == 11 and crv == inter.crvs[1]:
            pts = divide_curve_manually(crv, [0.5])
        elif (inter.layer == "11-09" or inter.layer == "09-11") and box_number == 11:
            pts = divide_curve_manually(crv, [0.7])
        elif (inter.layer == "07-08" or inter.layer == "08-07") and box_number == 11:
            pts = divide_curve_manually(crv, [0.25,0.55, 0.85])
        elif (inter.layer == "08-IT" or inter.layer == "IT-08") and box_number == 11:
            pts = divide_curve_manually(crv, [0.13,0.30, 0.67,0.85])
        elif (inter.layer == "00-IL" or inter.layer == "IL-00") and box_number == 11:
            pts = divide_curve_manually(crv, [])
       
        elif (inter.layer == "11-06" or inter.layer == "06-11") and box_number == 10:
            pts = divide_curve_manually(crv, [0.5])
        elif (inter.layer == "07-01" or inter.layer == "01-07") and box_number == 10:
            pts = divide_curve_manually(crv, [0.5])
        elif (inter.layer == "09-01" or inter.layer == "01-09") and box_number == 10 and crv == inter.crvs[0]:
            pts = divide_curve_manually(crv, [0.2,0.45,0.7])
        elif (inter.layer == "09-01" or inter.layer == "01-09") and box_number == 10 and crv == inter.crvs[1]:
            pts = divide_curve_manually(crv, [0.58])

        elif (inter.layer == "BO-07" or inter.layer == "07-BO") and box_number == 18 and crv == inter.crvs[1]:
            pts = divide_curve_manually(crv, [])
        elif (inter.layer == "BO-07" or inter.layer == "07-BO") and box_number == 18 and crv == inter.crvs[0]:
            pts = divide_curve_manually(crv, [0.1,0.3,0.5,0.7,0.9])
        
        elif (inter.layer == "09-04" or inter.layer == "04-09") and box_number == 18:
            pts = divide_curve_manually(crv, [0.25, 0.65])
        elif (inter.layer == "10-04" or inter.layer == "04-10") and box_number == 18:
            pts = divide_curve_manually(crv, [0.25, 0.65])
        elif (inter.layer == "11-IT" or inter.layer == "IT-11") and box_number == 18:
            pts = divide_curve_manually(crv, [0.2, 0.4,0.6, 0.8])

        #BOX 10: 11 AND 6, 07 AND 1 ADD 1 OR 2 BRACKETS, 09 AND 01 ADD 2 OR 3 
        # if list_is_provided:
        #     p_xs = [dx/crv.GetLength() for dx in distance]
        #     params, pts = [crv.DivideByLength(px) for px in p_xs]
        elif crv.GetLength() > distance*3:
            d_count = crv.GetLength()//distance
            params = crv.DivideByCount(d_count,True)
            pts = [crv.PointAt(t) for t in params[1:len(params)-1]]
        else:
            pts = [point]
        
        for pt in pts:
            #importnt!! could be used for the text !!
            pln = rg.Plane(pt,rg.Vector3d(end-point))
            #create circles that would intersect the 2 intersecting breps (as if we created a tube from the line of intersection)
            circ = rg.Circle(rg.Plane(pt,rg.Vector3d(end-point)),inter_radius).ToNurbsCurve()
            plane = rg.Brep.CreatePlanarBreps([circ])[0]
            #intersections of the circles patch with each intersecting panel 
            bpx0 = rg.Intersect.Intersection.BrepBrep(inter.breps[0],plane,0.001)
            bpx1 = rg.Intersect.Intersection.BrepBrep(inter.breps[1],plane,0.001)
            cutters = []
            if bpx0 and bpx1:
                cutters.extend([curve for curve in bpx0[1]])
                cutters.extend([curve for curve in bpx1[1]])
                #from the circle plane, split this circular surface into pcs
                cuts = plane.Split.Overloads[IEnumerable[rg.Curve], System.Double](cutters,0.001)
                #iterate over each surface cut
                i = 0
                for cut in cuts:
                    print("cut is : {0}".format(cut) )
                    circles.append(cut)
                    print(inter.layer)
                    count = 0
                    pcount = 0
                    flag = 0
                    #get the edges of a designated cut surface
                    for edge in cut.Edges:
                        count += 1
                        if edge.Degree == 1:
                            pcount += 1
                    #print(count)
                    if((inter.layer == "11-IL" or inter.layer == "IL-11") and box_number == 7):
                        max_area_threshold_applied = 240
                        p_count_max_applied = 10
                        min_area_threshold_applied = 70
                    elif((inter.layer == "11-IB" or inter.layer == "IB-11") and box_number == 7):                         
                        max_area_threshold_applied = 240
                        p_count_max_applied = 10
                        min_area_threshold_applied = 70
                    elif((inter.layer == "07-IB" or inter.layer == "IB-07") and box_number == 3 and pt != pts[2]):  
                        print("this should appear only twice")                       
                        max_area_threshold_applied = 240
                        p_count_max_applied = 13
                        min_area_threshold_applied = 110
                    
                    elif((inter.layer == "BO-07" or inter.layer == "07-BO") and box_number == 18):                       
                        max_area_threshold_applied = 240
                        p_count_max_applied = 13
                        min_area_threshold_applied = 112 #NEW!!

                    elif((inter.layer == "IB-11" or inter.layer == "11-IB") and box_number == 0):                       
                        max_area_threshold_applied = 240
                        p_count_max_applied = 13
                        min_area_threshold_applied = 209

                    elif((inter.layer == "IB-07" or inter.layer == "07-IB") and box_number == 18):                        
                        max_area_threshold_applied = 1
                        p_count_max_applied = 1
                        min_area_threshold_applied = 0.5

                    elif((inter.layer == "IR-11" or inter.layer == "11-IR") and box_number == 18): 
                        #print("kharaaaaaaaaaaaaaaaaaa")                        
                        max_area_threshold_applied = 220
                        p_count_max_applied = 13
                        min_area_threshold_applied = 218

                    
                    elif((inter.layer == "06-11" or inter.layer == "11-06") and box_number == 10): 
                        #print("kharaaaaaaaaaaaaaaaaaa")                        
                        max_area_threshold_applied = 150
                        p_count_max_applied = 13
                        min_area_threshold_applied = 140
                    
                    elif (inter.layer == "03-08" or inter.layer == "03-08") and box_number == 26:
                        print("shittt")
                        max_area_threshold_applied = 250
                        min_area_threshold_applied = 150
                        p_count_max_applied = 20

                    elif (inter.layer == "09-11" or inter.layer == "11-09") and box_number == 5:
                        print("shittt")
                        max_area_threshold_applied = 250
                        min_area_threshold_applied = 120
                        p_count_max_applied = 20

                    elif (inter.layer == "IR-05" or inter.layer == "05-IR") and box_number == 17:
                        print("shittt")
                        max_area_threshold_applied = 250
                        min_area_threshold_applied = 140
                        p_count_max_applied = 20


                    else:
                        max_area_threshold_applied = max_area_threshold
                        p_count_max_applied = pcount_max
                        min_area_threshold_applied =  threshold

                    #print("count is {0}, cut area is {1} and pcount is {2} and max threshold is {3}".format(count, cut.GetArea(), pcount,max_area_threshold_applied ))
                    if (count > 4 and cut.GetArea() > min_area_threshold_applied and cut.GetArea() < max_area_threshold_applied and pcount > 4 and pcount < p_count_max_applied) : #pcount < 7 was added to account for any irregularites 
                        print("kharaaaaa22")
                        #of brackets that may cause problems!!                        
                        edge_curves = [edge.EdgeCurve for edge in cut.Edges if edge.Degree == 1]
                        edge_curves.sort(key = lambda e :e.GetLength())
                        #circles.append(edge_curves)
                        edge_count = 0
                        big_edge = edge_curves[-1]
                        for e in edge_curves:
                            edge_count +=1
                        small_edge = None
                        p0 = None
                        p1 = None
                        pp0 = None
                        pp1 = None

                        if(inter.layer == "03-08" or inter.layer == "08-03" and box_number == 26):
                            if cut.GetArea() < 190:
                                continue
                            for curve in edge_curves:
                                pt_st = curve.PointAtStart
                                pt_end = curve.PointAtEnd
                                line = rg.Line(pt_st, pt_end)
                                if line.Length > 12 and line.Length < 13:
                                    big_edge = curve
                                if line.Length > 5.9 and line.Length < 6.1:
                                    edge_curves = [curve]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(edge_curves[0], big_edge, 100)
                        
                        elif((inter.layer == "IB-07" or inter.layer == "07-IB") and box_number == 3 and pt != pts[2]):
                            if cut.GetArea() < 190:
                                continue
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[-1]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        
                        elif((inter.layer == "10-IL" or inter.layer == "IL-10") and box_number == 3):
                            small_edge = edge_curves[4]
                            #big_edge = edge_curves[8]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        
                        elif((inter.layer == "BA-02" or inter.layer == "02-BA") and box_number == 26):
                            if cut.GetArea() > 125 or cut.GetArea() < 110:
                                continue
                            small_edge = edge_curves[2]
                            big_edge = edge_curves[5]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        
                        elif((inter.layer == "05-IL" or inter.layer == "IL-05") and box_number == 7):
                            continue
                        
                        elif((inter.layer == "11-IB" or inter.layer == "IB-11") and box_number == 7):
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        
                        elif((inter.layer == "11-IL" or inter.layer == "IL-11") and box_number == 7):
                            small_edge = edge_curves[4]
                            big_edge = edge_curves[8]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)                     
                        
                        elif((inter.layer == "BO-07" or inter.layer == "07-BO") and box_number == 18):
                            print("we are kharuyanaaa")
                            #curve = rg.Curve.JoinCurves([edge_curves[3],edge_curves[4]])[0]
                            small_edge = edge_curves[2]
                            print(len(edge_curves))
                            big_edge = edge_curves[5]
                            #big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                            big_edge = rg.Line(pp1, pp0)
                            big_edge = big_edge.ToNurbsCurve()
                            pp0 = big_edge.PointAtStart
                            pp1 = big_edge.PointAtEnd

                        elif((inter.layer == "IB-11" or inter.layer == "11-IB") and box_number == 0): 
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        

                        elif((inter.layer == "IR-11" or inter.layer == "11-IR") and box_number == 18): 
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        

                        elif((inter.layer == "06-11" or inter.layer == "11-06") and box_number == 10): 
                            print("kharaaaaaaa")
                            small_edge = edge_curves[5]
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        
                        elif((inter.layer == "09-11" or inter.layer == "11-09") and box_number == 5): 
                            print("kharaaaaaaa")
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[5]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        


                        else:
                            #big_edges.append(big_edge)
                            print(inter.layer)
                            small_edge, big_edge, p0, p1, pp0, pp1, edge3 = select_small_edge_and_adjust_both_edges(edge_curves, big_edge)
                        
                        
                        
                        #add a plane for adding later on the appropriate tags
                        planes_pair, px, py = add_planes_for_textv2(p0, p1, pp0, pp1, 3, move_text_distance1, move_text_distance2) #both planes are appended
                        planes_pair_brkts, _, _ = add_planes_for_text(p0, p1, pp0, pp1, move_text_4_brkt_1, move_text_4_brkt_2)
                        #Kept part of Ananyas code
                        vec = rg.Vector3d(p1 - p0)
                        line = rg.Line(p0,vec,25.15).ToNurbsCurve() #0.15 Fab_tol
                        small_edge = line
                        vec1 = rg.Vector3d(pp1 - pp0)
                        line1 = rg.Line(pp0,vec1,25.15).ToNurbsCurve() #0.15 used to be Fab_tol
                        big_edge = line1
                        #GET THE MIDPOINT OF THE BIGEDGE?
                        big_edge.Domain = rg.Interval(0,1)
                        c_pt = big_edge.PointAt(0.5)
                        closest_pt0 = (inter.breps[0]).ClosestPoint(c_pt,1.0) 
                        closest_pt1 = (inter.breps[1]).ClosestPoint(c_pt,1.0)
                        
                        p1s.append(closest_pt0[5])
                        guide_vec = (closest_pt0[5]) if (closest_pt0[0]) else None
                        
                        sm_edges.append(small_edge)
                        big_edges.append(pp0)
                        #push back big_edge
                        box_type = 0
                        #check if the connection is between a box and a panel
                        if not (inter.layer.Split('-')[0] in B_TAGS or inter.layer.Split('-')[1] in B_TAGS):
                            if guide_vec is None and closest_pt1[0] :
                                guide_vec = closest_pt1[5]
                            #print (guide_vec)
                            guide_vec.Unitize()
                            guide_vec *= -3.20
                            
                            big_edge.Translate(guide_vec)

                        else:
                            box_type = 1

                        
                        big_edge, pp0, pp1 = final_adjustment_big_edge(small_edge, big_edge, 200)
                        if box_type == 1: #meaning one of the breps is wooden box side
                            small_edge, big_edge, p0, p1, pp0, pp1, depth_vector =  inter.adjustment_box_bracket(small_edge, big_edge, p0, p1, pp0, pp1)
                        print("sm edge typeis {0}".format(type(small_edge)))
                        small_edge_tol, big_edge_tol, p0, p1_t, pp0, pp1_t = inter.adjust_small_big_edge_for_fab_tolerance(small_edge, big_edge, p0, p1, pp0, pp1, FAB_TOL)
                        
                        p0s.append(small_edge_tol)
                        p1s.append(p1)
                        pp0s.append(big_edge_tol)
                        pp1s.append(p1_t)
                        if small_edge and big_edge is not None:
                            fil = rg.Curve.CreateFilletCurves(small_edge,p0,big_edge,pp0,0,True,True,True,True,0.01)
                            fil_tol = rg.Curve.CreateFilletCurves(small_edge_tol,p0,big_edge_tol,pp0,0,True,True,True,True,0.01)
                            #p1s.append(fil[0])
                            
#                            rg.PolyCurve.SegmentCurve
                            if fil[0].SegmentCount<2 or min([fil[0].SegmentCurve(i).GetLength() for i in range(fil[0].SegmentCount)])<20:
                                #print ('fli')
                                fil = rg.Curve.CreateFilletCurves(small_edge,p0,big_edge, pp1,0,True,True,True,True,0.01)
                                fil_tol = rg.Curve.CreateFilletCurves(small_edge_tol,p0,big_edge_tol, pp1_t,0,True,True,True,True,0.01)
                            fil = fil[0] if len(fil)==1 else None
                            fil_tol = fil_tol[0] if len(fil_tol)==1 else None
                            
                            off = fil.Offset(rg.Point3d((fil.PointAtEnd+fil.PointAtStart)/2),rg.Plane(fil.PointAtEnd,fil.PointAtStart,fil.PointAt(0.5)).ZAxis,3.2,0.01,0.01,False,rg.CurveOffsetCornerStyle.Sharp,rg.CurveOffsetEndStyle.Flat)
                            off_tol = fil_tol.Offset(rg.Point3d((fil_tol.PointAtEnd+fil_tol.PointAtStart)/2),rg.Plane(fil_tol.PointAtEnd,fil_tol.PointAtStart,fil_tol.PointAt(0.5)).ZAxis,3.2,0.01,0.01,False,rg.CurveOffsetCornerStyle.Sharp,rg.CurveOffsetEndStyle.Flat)
                            #sm_edges.append(off[0])
                            
                            # if not box_type: 
                            #     b1,b2 = rg.Extrusion.Create(off[0].ToNurbsCurve(),9.15, True),rg.Extrusion.Create(off[0].ToNurbsCurve(),-9.15,True) #X_FAB TOL 
                            #     b1_t,b2_t = rg.Extrusion.Create(off_tol[0].ToNurbsCurve(),9.15 - FAB_TOL, True),rg.Extrusion.Create(off_tol[0].ToNurbsCurve(),-9.15 + FAB_TOL,True)
                            #     inter.br_type.append(1)
                            #else: 
                            b1,b2 = rg.Extrusion.Create(off[0].ToNurbsCurve(),15.15, True),rg.Extrusion.Create(off[0].ToNurbsCurve(),-15.15,True) #X_FAB_TOL
                            b1_t,b2_t = rg.Extrusion.Create(off_tol[0].ToNurbsCurve(),15.15 - FAB_TOL, True),rg.Extrusion.Create(off_tol[0].ToNurbsCurve(),-15.15 + FAB_TOL,True)
                            inter.br_type.append(0)
                            #sm_edges.append(b1_t)
                            #big_edges.append(b1)
                            if b1 and b2 is not None:
                                x1 = b1.ToBrep()
                                x2 = b2.ToBrep()
                                x1_t = b1_t.ToBrep()
                                x2_t = b2_t.ToBrep()
                                bool = rg.Brep.CreateBooleanUnion([x1,x2],0.001)
                                bool_t = rg.Brep.CreateBooleanUnion([x1_t,x2_t],0.001)
                                if len(bool)==1:
                                    bool[0].MergeCoplanarFaces(0.00,0.001)
                                    bool_t[0].MergeCoplanarFaces(0.00,0.001)
                                    bool = bool[0]
                                    bool_t = bool_t[0]
                                else:
                                    print ('Boolean not created, check breps')
                            else:
                                print ('Bad Offset Curve, Extrusion not created.')
                            fillet_indices = []
                            fillet_indices_tol = []
                            #sm_edges.append(fil)
                            for edge in bool.Edges:
                                if abs(edge.EdgeCurve.GetLength() - 3.2) < 0.5:
                                    num =  edge.EdgeIndex
                                    fillet_indices.append(num)
                            for edge_t in bool_t.Edges:
                                if abs(edge_t.EdgeCurve.GetLength() - 3.2) < 0.5:
                                    num =  edge_t.EdgeIndex
                                    fillet_indices_tol.append(num)
                            indices = fillet_indices
                            indices_tol = fillet_indices_tol
                            bbe = rg.Brep.CreateFilletEdges(bool,indices,[2.0 for _ in range(len(indices))],[2.0 for _ in range(len(indices))],rg.BlendType.Fillet,rg.RailType.RollingBall,0.0001)
                            bbe_tol = rg.Brep.CreateFilletEdges(bool_t,indices_tol,[4.0 for _ in range(len(indices_tol))],[4.0 for _ in range(len(indices_tol))],rg.BlendType.Fillet,rg.RailType.RollingBall,0.0001)
                           

                            #new part to accomodate the screws in the top box panels 
                            if box_type == 1 and ("TO" in inter.layer or "IT" in inter.layer):
                                screw, face, cntr_pt = inter.create_screws_holes(bbe_tol[0], depth_vector)
                                screw_cntr_pts.append(cntr_pt)
                                #bracket_lines_tol.append(fil_tol) 
                                top_box_brackets.append(bbe_tol[0])
                                hexholder, face = inter.create_hexholder(bbe_tol[0], depth_vector)
                                print(hexholder)
                                temp = rg.Brep.CreateBooleanUnion([bbe_tol[0], hexholder], 0.001)
                                temp2 = rg.Brep.CreateBooleanDifference(temp[0], screw, 0.001)
                                bbe_tol[0] = temp2[0]
                                inter.hexholders.append(hexholder)
                                #sm_edges.append(face)
                                inter.screws.append(screw)

                            if box_type == 1 and ("RI" in inter.layer):
                                debug_panels.append(bbe_tol[0])
                                bracket_lines_tol.append(fil_tol) 
                                

                        #add the real bracket to the intersection variable brackets
                        if "00" in inter.layer  and "TO" in inter.layer and i == 0:
                            print('i is : {0}'.format(i)) 
                        elif "00" in inter.layer and "RI" in inter.layer and i == 3:
                            print('i is : {0}'.format(i)) 
                        else:
                            bbe = bbe[0]
                            bbe_tol = bbe_tol[0]
                            #circs.append([small_edge,big_edge,cut])
                            circs.append(bbe)
                            circs_tol.append(bbe_tol)
                            inter.text_planes.append(planes_pair)
                            inter.text_planes_brkts.append(planes_pair_brkts)
                            inter.brackets.append(bbe)
                            
                            inter.fab_brackets.append(bbe_tol)
                            
                            tags.append(inter.layer)

                            box_tag = ""
                            if box_number < 10:
                                box_tag = "0{0}".format(box_number)
                            else:
                                box_tag = "{0}".format(box_number)

                            bracket_tag = ""
                            if bracket_index < 10:
                                bracket_tag = "0{0}".format(bracket_index)
                            else:
                                bracket_tag = "{0}".format(bracket_index)
                            
                            
                            inter.tags.append("{0}-{1}-{2}".format(box_tag,inter.layer,bracket_tag))
                            bracket_index += 1
                    i += 1 
    if len(inter.text_planes) > 0:
        planes_.append(inter.text_planes)
    
sc.doc = doc

for tag in tags:
    #print("tag type is {0}".format(type(tag)))
    if tag.Split('-')[0] in B_TAGS or tag.Split('-')[1] in B_TAGS:
        pass

planes_txt = []
planes_txt_for_brkt = []
tag_txt_for_brkt = []
tag_txt_by_layer = []
tag_txt_layers = []
tag_txt = []
all_brackets = []
all_fab_brackets = []
all_screws = []
all_br_types = []

all_hexholders = []

for inter in intersections:
    all_brackets.append(inter.brackets)
    all_fab_brackets.append(inter.fab_brackets)
    all_screws.append(inter.screws)
    all_hexholders.append(inter.hexholders)
    all_br_types.append(inter.br_type)
    for index, planes_pair in enumerate(inter.text_planes): 
        j = 0
        pt0 =inter.breps[0].ClosestPoint(planes_pair[0].Origin)
        pt1 =inter.breps[0].ClosestPoint(planes_pair[1].Origin)
        dist0 = planes_pair[0].Origin.DistanceTo(pt0)
        dist1 = planes_pair[1].Origin.DistanceTo(pt1) 
        tag_txt_for_brkt.append(inter.tags[index])      
        if dist1 < dist0:
            planes_pair.reverse()  
            inter.text_planes_brkts[index].reverse()  
        for i, plane in enumerate(planes_pair):
            if not inter.layer.Split('-')[i] in B_TAGS:
                tag_txt_layers.append(inter.layer.Split('-')[i])
                planes_txt.append(plane)
                tag_txt.append(inter.tags[index]) 
                # if j == 0 and dist1> dist0:
                #     planes_txt_for_brkt.append(inter.text_planes_brkts[index][i])                   
                #     j += 1
                if (j== 0 and dist1 > dist0):
                    planes_txt_for_brkt.append(inter.text_planes_brkts[index][0])                   
                    j += 1
                elif (j==0 and dist1 < dist0):
                    planes_txt_for_brkt.append(inter.text_planes_brkts[index][1])
                    j += 1

                

        
       
            

panel_extrusion = Panel_Extrusions(intersections)
dibond_panels =  panel_extrusion.populate_brackets_extrusion()
all_panels = panel_extrusion.panels



if bake_panels:
    for panel, id in zip(panel_extrusion.panels, panel_extrusion.panels_ids):
        if id not in B_TAGS:
            bake_object_v2(panel, id, parent_layer_name)


intersections = intersections
circs = tree(circs)
circs_tol = tree(circs_tol)
all_fab_brackets = tree(all_fab_brackets)


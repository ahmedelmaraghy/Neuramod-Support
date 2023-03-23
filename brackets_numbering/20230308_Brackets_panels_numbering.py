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
    
    sub_parent_index = sc.doc.Layers.Find("{0}_panels_fabri_ready".format(parent_layer_name), True)
    if sub_parent_index < 0:
        sub_parent_layer = rd.Layer()
        sub_parent_layer.ParentLayerId = parent_layer.Id
        sub_parent_layer.Name = "{0}_panels_fabri_ready".format(parent_layer_name)
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

    return big_edge.ToNurbsCurve(), big_edge.From


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

class Panel_Extrusions(object):
    def __init__(self,intersections):
        self.intersections = intersections
        self.panels = []
        self.panels_ids = []

    def populate_brackets_extrusion(self):
        """iterates over all panels and checks if they are in the list or not, if yes, 
        then perform 
        """
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

                #return new_brep, bracket
    


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
        self.text_planes = []
        self.tags = []
        self.brackets = []
        self.label1 = TextEntity()
        self.label2 = TextEntity()

    def remove_brackets_from_panel(self, brep):
        """
        produces the final panel where the brackets are split from the panel, producing the final trimmed panel only from one side of brackets
        """
        original_brep = brep
        
        for bracket in self.brackets: 
            if((rg.Brep.CreateBooleanDifference(original_brep, bracket, 0.001)).Count> 0):
                original_brep = rg.Brep.CreateBooleanDifference(original_brep, bracket, 0.001)[0]
            

        return original_brep
   

FAB_TOL = 0.15

B_TAGS = ('TO','BO','LF','RI','BA','IT','IB','IL','IR')

inter_radius = 10.0
intersections = []

circles = []
sm_edges = []
big_edges = []
p0s = []
p1s = []
planes_ = []
edges_3 = []

#get the intersection curves (line likes) between each brep and the ther other 
for brep0,id0 in zip(breps,ids):
    layer0 = GetObjectLayer(id0) #layer0 is the name of the layer of the baked brep in the actual rhino file
    #print("layer 0 is {0}".format(layer0))
    for brep1,id1 in zip(breps,ids):
        layer1 = GetObjectLayer(id1)
        #print("layer 1 is {0}".format(layer1))
        if (brep0 is not brep1) and (("%s-%s"%(layer0,layer1) not in [int.layer for int in intersections])) and (("%s-%s"%(layer1,layer0) not in [int.layer for int in intersections])) and (layer1 not in B_TAGS or layer0 not in B_TAGS):
            #print ("%s-%s"%(layer0,layer1)),"%s-%s"%(layer1,layer0), [int.layer for int in intersections]
            if(((layer0 == "03" and layer1 == "04") or (layer0 == "04" and layer1 == "03") and (box_number == 5))
               or ((layer0 == "01" and layer1 == "04") or (layer0 == "04" and layer1 == "01") and (box_number == 5))):
                print("we CHANGED TOL")
                actual_inter_tol = 1.0
            elif((layer0 == "06" and layer1 == "10") or (layer0 == "10" and layer1 == "06") and (box_number == 5)):
                actual_inter_tol = 1.5
           
            else:
                actual_inter_tol = inter_tol_breps 
            if layer1 in B_TAGS or layer0 in B_TAGS:
                if((layer0 == "BO" and layer1 == "07") or (layer0 == "07" and layer1 == "BO") and (box_number == 18)):
                    actual_inter_tol += 0.6
            else:
                actual_inter_tol += add_B_tol
            bbx = rg.Intersect.Intersection.BrepBrep(brep0,brep1,actual_inter_tol)
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


circs,tags = [],[]
max_area_threshold_applied = max_area_threshold
min_area_threshold_applied = threshold
p_count_max_applied = pcount_max

for inter in intersections:
    bracket_index = 0
    for crv in inter.crvs:
        #checks if curve is long enough to put more than 1 bracket or can only fit no more than 1 bracket only
        #new!! setting domain to be in between 0 and 1
        crv.Domain = rg.Interval(0,1)
        ts =  crv.DivideByCount(2,True)
        #print("domain is {0} and {1}".format(ts[1], ts[2]))
        point,end = crv.PointAt(ts[1]),crv.PointAt(ts[2])
        if crv.GetLength() > distance*3:
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
                    #circles.append(cut)
                    print(inter.layer)
                    count = 0
                    pcount = 0
                    flag = 0
                    #get the edges of a designated cut surface
                    for edge in cut.Edges:
                        count += 1
                        if edge.Degree == 1:
                            pcount += 1
                    print(count)
                    if(inter.layer == "11-IL" or inter.layer == "IL-11" and box_number == 7):
                        max_area_threshold_applied = 240
                        p_count_max_applied = 10
                        min_area_threshold_applied = 70
                    elif(inter.layer == "11-IB" or inter.layer == "IB-11" and box_number == 7):                         
                        max_area_threshold_applied = 240
                        p_count_max_applied = 10
                        min_area_threshold_applied = 70
                    elif(inter.layer == "07-IB" or inter.layer == "IB-07" and box_number == 3):                         
                        max_area_threshold_applied = 240
                        p_count_max_applied = 13
                        min_area_threshold_applied = 110
                    
                    elif(inter.layer == "BO-07" or inter.layer == "07-BO" and box_number == 18): 
                        #print("kharaaaaaaaaaaaaaaaaaa")                        
                        max_area_threshold_applied = 240
                        p_count_max_applied = 13
                        min_area_threshold_applied = 120


                    else:
                        max_area_threshold_applied = max_area_threshold
                        p_count_max_applied = pcount_max
                        min_area_threshold_applied =  threshold

                    #print("count is {0}, cut area is {1} and pcount is {2} and max threshold is {3}".format(count, cut.GetArea(), pcount,max_area_threshold_applied ))
                    if (count > 4 and cut.GetArea() > min_area_threshold_applied and cut.GetArea() < max_area_threshold_applied and pcount > 4 and pcount < p_count_max_applied) : #pcount < 7 was added to account for any irregularites 
                        #of brackets that may cause problems!!                        
                        edge_curves = [edge.EdgeCurve for edge in cut.Edges if edge.Degree == 1]
                        edge_curves.sort(key = lambda e :e.GetLength())
                        circles.append(edge_curves)
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
                            print("we are khara")
                            #print(inter.layer)
                            for curve in edge_curves:
                                pt_st = curve.PointAtStart
                                pt_end = curve.PointAtEnd
                                line = rg.Line(pt_st, pt_end)
                                if line.Length > 12 and line.Length < 13:
                                    big_edge = curve
                                if line.Length > 5.9 and line.Length < 6.1:
                                    edge_curves = [curve]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(edge_curves[0], big_edge, 100)
                        elif(inter.layer == "IB-07" or inter.layer == "07-IB" and box_number == 3):
                            if cut.GetArea() < 190:
                                continue
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[-1]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        elif(inter.layer == "10-IL" or inter.layer == "IL-10" and box_number == 3):
                            small_edge = edge_curves[4]
                            #big_edge = edge_curves[8]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        elif(inter.layer == "BA-02" or inter.layer == "02-BA" and box_number == 26):
                            if cut.GetArea() > 125 or cut.GetArea() < 110:
                                continue
                            small_edge = edge_curves[2]
                            big_edge = edge_curves[5]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        elif(inter.layer == "05-IL" or inter.layer == "IL-05" and box_number == 7):
                            continue
                        elif(inter.layer == "11-IB" or inter.layer == "IB-11" and box_number == 7):
                            small_edge = edge_curves[3]
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        elif(inter.layer == "11-IL" or inter.layer == "IL-11" and box_number == 7):
                            small_edge = edge_curves[4]
                            big_edge = edge_curves[8]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                      
                        
                        
                        elif(inter.layer == "BO-07" or inter.layer == "07-BO" and box_number == 18):
                            print("we are kharuyanaaa")
                            curve = rg.Curve.JoinCurves([edge_curves[3],edge_curves[4]])[0]
                            small_edge = curve
                            big_edge = edge_curves[7]
                            small_edge, big_edge, p0, p1, pp0, pp1 = select_small_edge_and_adjust_both_edges_exceptions(small_edge, big_edge, 100)
                        

                        
                        else:
                            big_edges.append(big_edge)
                            print(inter.layer)
                            small_edge, big_edge, p0, p1, pp0, pp1, edge3 = select_small_edge_and_adjust_both_edges(edge_curves, big_edge)
                        
                        
                        sm_edges.append(small_edge)
                        big_edges.append(big_edge)
                        p0s.append(pp0)
                        #new way for selecting the small edge is to join the curves and select the third one in the list:
                        
                       

                        #add a plane for adding later on the appropriate tags
                        planes_pair, px, py = add_planes_for_text(p0, p1, pp0, pp1, move_text_distance1, move_text_distance2) #both planes are appended

                        #edges_3.append(edge3)
                        #Kept part of Ananyas code
                        vec = rg.Vector3d(p1 - p0)
                        line = rg.Line(p0,vec,25.0 + FAB_TOL).ToNurbsCurve()
                        small_edge = line
                        vec1 = rg.Vector3d(pp1 - pp0)
                        line1 = rg.Line(pp0,vec1,25.0 + FAB_TOL).ToNurbsCurve()
                        big_edge = line1
                        #GET THE MIDPOINT OF THE BIGEDGE?
                        big_edge.Domain = rg.Interval(0,1)
                        c_pt = big_edge.PointAt(0.5)
                        closest_pt0 = (inter.breps[0]).ClosestPoint(c_pt,1.0) 
                        closest_pt1 = (inter.breps[1]).ClosestPoint(c_pt,1.0)
                        
                        p1s.append(closest_pt0[5])
                        guide_vec = (closest_pt0[5]) if (closest_pt0[0]) else None
                        
                        
                        #push back big_edge
                        box_type = 0
                        #check if the connection is between a box and a panel
                        if not (inter.layer.Split('-')[0] in B_TAGS or inter.layer.Split('-')[1] in B_TAGS):
                            if guide_vec is None and closest_pt1[0] :
                                guide_vec = closest_pt1[5]
                            print (guide_vec)
                            guide_vec.Unitize()
                            guide_vec *= -3.20
                            
                            big_edge.Translate(guide_vec)

                        else:
                            box_type = 1
                        


                        big_edge, pp0 = final_adjustment_big_edge(small_edge, big_edge, 200)
                        sm_edges.append(small_edge)
                        big_edges.append(big_edge)
                        p0s.append(pp0)
                        p1s.append(pp1)
                        if small_edge and big_edge is not None:
                            fil = rg.Curve.CreateFilletCurves(small_edge,p0,big_edge,pp0,0,True,True,True,True,0.01)
                            p1s.append(fil[0])
                            
#                            rg.PolyCurve.SegmentCurve
                            if fil[0].SegmentCount<2 or min([fil[0].SegmentCurve(i).GetLength() for i in range(fil[0].SegmentCount)])<20:
                                #print ('fli')
                                fil = rg.Curve.CreateFilletCurves(small_edge,p0,big_edge, pp1,0,True,True,True,True,0.01)
                            fil = fil[0] if len(fil)==1 else None
                            
                            off = fil.Offset(rg.Point3d((fil.PointAtEnd+fil.PointAtStart)/2),rg.Plane(fil.PointAtEnd,fil.PointAtStart,fil.PointAt(0.5)).ZAxis,3.2,0.01,0.01,False,rg.CurveOffsetCornerStyle.Sharp,rg.CurveOffsetEndStyle.Flat)
                            if not box_type: b1,b2 = rg.Extrusion.Create(off[0].ToNurbsCurve(),9.0 + FAB_TOL, True),rg.Extrusion.Create(off[0].ToNurbsCurve(),-9.0 - FAB_TOL,True)
                            else : b1,b2 = rg.Extrusion.Create(off[0].ToNurbsCurve(),15.0 + FAB_TOL, True),rg.Extrusion.Create(off[0].ToNurbsCurve(),-15.0 - FAB_TOL,True)
                            if b1 and b2 is not None:
                                x1 = b1.ToBrep()
                                x2 = b2.ToBrep()
                                bool = rg.Brep.CreateBooleanUnion([x1,x2],0.001)
                                if len(bool)==1:
                                    bool[0].MergeCoplanarFaces(0.00,0.001)
                                    bool = bool[0]
                                else:
                                    print ('Boolean not created, check breps')
                            else:
                                print ('Bad Offset Curve, Extrusion not created.')
                            fillet_indices = []
                            
                            for edge in bool.Edges:
                                if abs(edge.EdgeCurve.GetLength() - 3.2) < 0.5:
                                    num =  edge.EdgeIndex
                                    fillet_indices.append(num)
                            indices = fillet_indices
                            bbe = rg.Brep.CreateFilletEdges(bool,indices,[2.0 for _ in range(len(indices))],[2.0 for _ in range(len(indices))],rg.BlendType.Fillet,rg.RailType.RollingBall,0.0001)

                        #qadd the real bracket to the intersection variable brackets
                        if "00" in inter.layer  and "TO" in inter.layer and i == 0:
                            print('i is : {0}'.format(i)) 
                        elif "00" in inter.layer and "RI" in inter.layer and i == 3:
                            print('i is : {0}'.format(i)) 
                        else:
                            bbe = bbe[0]
                            circs.append([small_edge,big_edge,cut])
                            circs.append(bbe)
                            inter.text_planes.append(planes_pair)
                            inter.brackets.append(bbe)
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
tag_txt_by_layer = []
tag_txt_layers = []
tag_txt = []
all_brackets = []
for inter in intersections:
    all_brackets.append(inter.brackets)
    for index, planes_pair in enumerate(inter.text_planes): 

        pt0 =inter.breps[0].ClosestPoint(planes_pair[0].Origin)
        pt1 =inter.breps[0].ClosestPoint(planes_pair[1].Origin)
        dist0 = planes_pair[0].Origin.DistanceTo(pt0)
        dist1 = planes_pair[1].Origin.DistanceTo(pt1)
        if dist1 < dist0:
            planes_pair.reverse()
        for i, plane in enumerate(planes_pair):
             if not inter.layer.Split('-')[i] in B_TAGS:
                tag_txt_layers.append(inter.layer.Split('-')[i])
                planes_txt.append(plane)
                tag_txt.append(inter.tags[index]) 

        
       
            

panel_extrusion = Panel_Extrusions(intersections)
panel_extrusion.populate_brackets_extrusion()
all_panels = panel_extrusion.panels



if bake_panels:
    for panel, id in zip(panel_extrusion.panels, panel_extrusion.panels_ids):
        if id not in B_TAGS:
            bake_object_v2(panel, id, parent_layer_name)


intersections = intersections
circs = tree(circs)

# if bake:
#     for part,tag in zip(circs,tags):
#         bake_object(part,tag)

# for inter in intersections:
    #         planes_txt.append(inter.text_planes[0])
    #         planes_txt.append(inter.text_planes[1])
            # tag_txt.append(inter.tag)
            # tag_txt.append(inter.tag)
            # inter.label1.Text = inter.tag
            # inter.label2.Text = inter.tag
            # inter.label1.Justification = TextJustification.MiddleCenter
            # inter.label2.Justification = TextJustification.MiddleCenter
            # inter.label1.FontIndex = doc.Fonts.FindOrCreate("Arial", False, False)
            # inter.label2.FontIndex = doc.Fonts.FindOrCreate("Arial", False, False)
            # inter.label1.Plane = inter.text_planes[0]       
            # inter.label2.Plane = inter.text_planes[1]

            # print(inter.label2.Text)
            # doc.Objects.AddText(inter.label1)
            # doc.Objects.AddText(inter.label2)
            # doc.Views.Redraw()

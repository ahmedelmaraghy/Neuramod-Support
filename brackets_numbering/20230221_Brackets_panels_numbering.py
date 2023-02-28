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

def remove_duplicate_lines_from_polycurve(polycurve, tolerance):
    """Removes the duplicates of intersection lines that may occur when intersecting the 2 breps
    """
    # create a list to store the unique lines
    lines = []
    for curve in polycurve.Explode():
        #print("curve is linear : {0}".format(curve.IsLinear()))
        if curve.GetLength() > 20:
            curve.Domain = rg.Interval(0,1)
            lines.append(curve)

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

def select_small_edge_and_adjust_both_edges(edge_curves, big_edge, edge_extention = 10):
    joined_crvs_list = []
    for curve in edge_curves:
        if curve is not big_edge:
           joined_crvs_list.append(curve)

    curves = rg.Curve.JoinCurves(joined_crvs_list) 
    #print(curves)
    small_edge = None
    governing_edge = None
    long_gov_edge = joined_crvs_list[-1] #longest
    if curves.Count == 1:
       edges = curves[0].DuplicateSegments()
       small_edge = edges[2]
       governing_edge = (edges[1]) if edges[1].GetLength() > edges[3].GetLength() else (edges[3])

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
    
def add_planes_for_text(p0, p1, pp0, pp1, move_text_distance):
    """takes the points of the small and big line, creates planes for text insertion
    and moves it above of the brackets by a variable distance as preferred
    """
    small_Y = p1 - p0
    small_Y.Unitize()
    big_Y = pp1 - pp0
    big_Y.Unitize()

    small_X = rg.Vector3d.CrossProduct(small_Y, big_Y)
    big_X = rg.Vector3d.CrossProduct(big_Y, small_Y)

    small_origin = p1 + small_Y * move_text_distance
    big_origin = pp1 + big_Y * move_text_distance
    #create planes for both tags
    small_plane = rg.Plane(small_origin, small_X, small_Y)
    big_plane = rg.Plane(big_origin, big_X, big_Y)
    
    return [small_plane, big_plane], small_plane.Origin, big_plane.Origin




class Intersection(object):
    """Determines all data of intersection between layer and another layer 
        which means between one brep and another brep. 
        crvs: intersection lines
        Layer: name of the 2 layers in rhino string
        breps: actual breps list 
        layers: actual layers list         
    """
    def __init__(self,crvs,layer,breps,layers):
        self.crvs = crvs
        self.layer = layer
        self.layers = layers
        self.breps = breps
        self.text_planes = []
        self.tag = ""
        self.label1 = TextEntity()
        self.label2 = TextEntity()

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
    
#    displayColor = Rhino.Display.ColorRGBA(layerIndex)
    sc.doc.Objects.AddBrep(obj, attr)

FAB_TOL = 0.15

B_TAGS = ('TO','BO','LF','RI','BA','IT','IB','IL','IR')

inter_radius = 10.0


lines =  remove_duplicate_lines_from_polycurve(lines_list, dup_lines_tol)


intersections = []
#get the intersection curves (line likes) between each brep and the ther other 
for brep0,id0 in zip(breps,ids):
    layer0 = GetObjectLayer(id0) #layer0 is the name of the layer of the baked brep in the actual rhino file
    #print("layer 0 is {0}".format(layer0))
    for brep1,id1 in zip(breps,ids):
        layer1 = GetObjectLayer(id1)
        #print("layer 1 is {0}".format(layer1))
        if (brep0 is not brep1) and (("%s-%s"%(layer0,layer1) not in [int.layer for int in intersections])) and (("%s-%s"%(layer1,layer0) not in [int.layer for int in intersections])) and (layer1 not in B_TAGS or layer0 not in B_TAGS):
            #print ("%s-%s"%(layer0,layer1)),"%s-%s"%(layer1,layer0), [int.layer for int in intersections]
            bbx = rg.Intersect.Intersection.BrepBrep(brep0,brep1,inter_tol_breps)
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
                interX = Intersection(list_intersections,"%s-%s"%(layer0,layer1),[brep0,brep1],[layer0,layer1])
                intersections.append(interX)
circles = []
sm_edges = []
big_edges = []
p0s = []
edges_3 = []
#add a numbering for each bracket
#add a function that adds the plane and origin to which the number should be written 
#add finally for all intersecions adding the number in rhino 
#

circs,tags = [],[]
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
                for cut in cuts:
                    count = 0
                    pcount = 0
                    flag = 0
                    #get the edges of a designated cut surface
                    for edge in cut.Edges:
                        count += 1
                        if edge.Degree == 1:
                            pcount += 1
                    #print (cut.GetArea())
                    #if edges in a cut is more than 4 (dont fuckin know why),
                    #and if the area is more than a threshold 
                    if count > 4 and cut.GetArea() > threshold and pcount > 4 and pcount < 7: #pcount < 6 was added to account for any irregularites 
                        #of brackets that may cause problems!!
                        #circles.append(cut)
                        edge_curves = [edge.EdgeCurve for edge in cut.Edges if edge.Degree == 1]
                        edge_curves.sort(key = lambda e :e.GetLength())
                        circles.append(edge_curves)
                        edge_count = 0
                        big_edge = edge_curves[-1]
                        for e in edge_curves:
                            #change from Ananya's code
                            #if abs(e.GetLength() - inter_radius) < 0.1: #!!! why 0.1
                                #big_edge = e
                            edge_count +=1
                        #new way for selecting the small edge is to join the curves and select the third one in the list:
                        small_edge, big_edge, p0, p1, pp0, pp1, edge3 = select_small_edge_and_adjust_both_edges(edge_curves, big_edge)
                        

                        #add a plane for adding later on the appropriate tags
                        inter.text_planes, px, py = add_planes_for_text(p0, p1, pp0, pp1, move_text_distance) #both planes are appended
                        p0s.append(py)
                        #debugging
                        sm_edges.append(small_edge)
                        big_edges.append(big_edge)
                        edges_3.append(edge3)

                        #Kept part of Ananyas code
                        vec = rg.Vector3d(p1 - p0)
                        line = rg.Line(p0,vec,25.0 + FAB_TOL).ToNurbsCurve()
                        small_edge = line
                        vec1 = rg.Vector3d(pp1 - pp0)
                        line1 = rg.Line(pp0,vec1,25.0 + FAB_TOL).ToNurbsCurve()
                        big_edge = line1
                        big_edge.Domain = rg.Interval(0,1)
                        c_pt = big_edge.PointAt(0.5)
                        closest_pt0 = (inter.breps[0]).ClosestPoint(c_pt,1.0) 
                        closest_pt1 = (inter.breps[1]).ClosestPoint(c_pt,1.0)
                        guide_vec = (closest_pt0[5]) if (closest_pt0[0]) else None
                        
                        #push back big_edge
                        box_type = 0
                        if not (inter.layer.Split('-')[0] in B_TAGS or inter.layer.Split('-')[1] in B_TAGS):
                            if guide_vec is None and closest_pt1[0] :
                                guide_vec = closest_pt1[5]
                            #print (guide_vec)
                            guide_vec.Unitize()
                            guide_vec *= -3.20
                            big_edge.Translate(guide_vec)
                        else:
                            box_type = 1
                        if small_edge and big_edge is not None:
                            fil = rg.Curve.CreateFilletCurves(small_edge,p0,big_edge,pp0,0,True,True,True,True,0.01)
                            #print (fil)
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
                        bbe = bbe[0]
                        circs.append([small_edge,big_edge,cut])
                        circs.append(bbe)
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

                        inter.tag = "{0}-{1}-{2}".format(box_tag,inter.layer,bracket_tag)
                        print("{0}-{1}-{2}".format(box_tag,inter.layer,bracket_tag))
                        bracket_index += 1
    
sc.doc = doc



for tag in tags:
    #print("tag type is {0}".format(type(tag)))
    if tag.Split('-')[0] in B_TAGS or tag.Split('-')[1] in B_TAGS:
        pass

if bake:
    for part,tag in zip(circs,tags):
        bake_object(part,tag)
    for inter in intersections:
        if len(inter.text_planes) > 1:
            inter.label1.Text = inter.tag
            inter.label2.Text = inter.tag
            inter.label1.Justification = TextJustification.MiddleCenter
            inter.label2.Justification = TextJustification.MiddleCenter
            inter.label1.FontIndex = doc.Fonts.FindOrCreate("Arial", False, False)
            inter.label2.FontIndex = doc.Fonts.FindOrCreate("Arial", False, False)
            inter.label1.Plane = inter.text_planes[0]       
            inter.label2.Plane = inter.text_planes[1]

            print(inter.label2.Text)
            doc.Objects.AddText(inter.label1)
            doc.Objects.AddText(inter.label2)
            doc.Views.Redraw()

if bake_box:
    for part,tag in zip(circs,tags):
        if tag.Split('-')[0] in B_TAGS or tag.Split('-')[1] in B_TAGS:
            bake_object(part,tag)




        

        




 
    
sc.doc = ghdoc

intersections = intersections
circs = tree(circs)
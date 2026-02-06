# Posunout body vytvoř polygon
def moveLineGetPoly(p1, p2, dirX, dirY):
    # Jednoduchý úhel 45° o X a Y stejně přičíst
    p1m=arcpy.Point(p1.X+dirX, p1.Y+dirY)
    p2m=arcpy.Point(p2.X+dirX, p2.Y+dirY)
    # Z původních neposunutých a posunutých vytvoč polygon (4 body) 
    polygon = arcpy.Polygon(arcpy.Array([p1, p2, p2m, p1m]))
    return polygon
  
# Sjednotit - bez ukazování průběhu
def mergePolygones(polygons_to_merge):
    merged_polygon = None
    for polygon in polygons_to_merge:
        if merged_polygon is None:
            merged_polygon = polygon
        else:
            merged_polygon = merged_polygon.union(polygon)
    return merged_polygon
  
# Sjednotit - s průběhem
def mergePolygonesL(polygons_to_merge):
    arcpy.SetProgressorLabel("Merging...")
    arcpy.SetProgressor("step", "Merging shadow...", 0, len(polygons_to_merge), 1)
    merged_polygon = None
    for polygon in polygons_to_merge:
        arcpy.SetProgressorPosition()
        if merged_polygon is None:
            merged_polygon = polygon
        else:
            merged_polygon = merged_polygon.union(polygon)
    return merged_polygon
  
# Vytvořit stín
def create_shadow(input_layer, output_layer, len_shadow):
    # Postup
    rowcount = 0
    with arcpy.da.SearchCursor(input_layer, "*") as cursor:
        for row in cursor:
            rowcount = rowcount + 1
    arcpy.SetProgressor("step", "Creating shadow...", 0, rowcount, 1)
    
    # Otevřít cursor pro vkládanou vrstvu
    with arcpy.da.SearchCursor(input_layer, ["SHAPE@", "OID@"]) as cursor:
        # Otevřít Cursor pro výsledek
        with arcpy.da.InsertCursor(output_layer, ["SHAPE@", "S_ID"]) as ins_cursor:
            # / print("cursor:", cursor) /  # Debugging
            xId=0
            created_polygones=[]
            for row in cursor:                
                arcpy.SetProgressorPosition()
                shape = row[0]
                oid = row[1]
                vertices = shape.getPart(0)
                pt_len=len(vertices)
                pt_last=vertices[pt_len-2]
                # vytvořit polygony posunutých čar
                created_sub=[]
                for pt in vertices:
                    if not pt==None:
                        if not pt_last==None:
                            created=moveLineGetPoly(pt, pt_last, len_shadow, len_shadow)
                            created_sub.append(created)                                
                            pt_last=pt
                # Sub sjednocení jednoho objektu - polygony stínů čar (např jedna budova - 4 hray - 4 polygony stínu)
                sub=mergePolygones(created_sub);                
                created_polygones.append(sub)
            # Sjednocení všech objektů (více budov)
            polygones_merged=mergePolygonesL(created_polygones)
            ins_cursor.insertRow([polygones_merged, 0])
                
    # ukončit operaci
    edit.stopOperation()
    
    # ukončit úpravu
    edit.stopEditing(True)
  
if __name__ == "__main__":
    # Input parametery
    # / print("start") /  # Debugging
    input_layer = arcpy.GetParameterAsText(0)
    output_layer = arcpy.GetParameterAsText(1)
    
    #délka stínu
    sh_len = arcpy.GetParameter(2)
    
    # Kontrola názvu
    output_layer = arcpy.ValidateTableName(output_layer, arcpy.env.workspace)
    # Přepsat existující
    if arcpy.Exists(output_layer):
        edit = arcpy.da.Editor(arcpy.env.workspace)
        edit.startEditing(False, True)
        edit.startOperation()
        
        # Vyčistit
        with arcpy.da.UpdateCursor(output_layer, ["OID@"]) as del_cursor:
            for row in del_cursor:
                del_cursor.deleteRow()
        # Smazat cursor  
        del del_cursor
        
    # Vytvořit nové
    else:
        arcpy.CreateFeatureclass_management(arcpy.env.workspace, output_layer, "POLYGON", spatial_reference=input_layer)
        
        # Přidat id
        arcpy.AddField_management(output_layer, "S_ID", "LONG")
        
        # Otevřít a upravit
        edit = arcpy.da.Editor(arcpy.env.workspace)
        edit.startEditing(False, True)
        
        # Vytvořit novou operaci
        edit.startOperation()
    # Vygenerovat stín
    create_shadow(input_layer, output_layer, sh_len)

import json, urllib.request, urllib.parse
U="https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_OPENDATA_Cadastral_VTPARCELS_poly_standardized_parcels_SP_v1/FeatureServer/0/query"
F="SPAN,PARCID,PROPTYPE,OWNER1,OWNER2,ADDRGL1,CITYGL,STGL,ZIPGL,DESCPROP,LOCAPROP,CAT,RESCODE,ACRESGL,REAL_FLV,HSTED_FLV,NRES_FLV,LAND_LV,IMPRV_LV,E911ADDR,GLYEAR"
rows=[];off=0
while True:
    q=urllib.parse.urlencode({"where":"TNAME='MONTPELIER'","outFields":F,"returnGeometry":"true","returnCentroid":"true","geometryType":"esriGeometryEnvelope","outSR":4326,"resultOffset":off,"resultRecordCount":1000,"orderByFields":"OBJECTID","f":"json"})
    d=json.load(urllib.request.urlopen(U+"?"+q,timeout=60))
    fs=d["features"]
    for f in fs:
        a=f["attributes"];c=f.get("centroid") or {}
        a["lng"]=round(c["x"],6) if c else None;a["lat"]=round(c["y"],6) if c else None
        rows.append(a)
    off+=len(fs)
    if not fs or not d.get("exceededTransferLimit"):break
json.dump(rows,open("data.json","w"),separators=(",",":"))
print(len(rows))

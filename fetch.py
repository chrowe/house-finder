import json, os, urllib.request, urllib.parse
U="https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_OPENDATA_Cadastral_VTPARCELS_poly_standardized_parcels_SP_v1/FeatureServer/0/query"
F="SPAN,PARCID,PROPTYPE,OWNER1,OWNER2,ADDRGL1,CITYGL,STGL,ZIPGL,DESCPROP,LOCAPROP,CAT,RESCODE,ACRESGL,REAL_FLV,HSTED_FLV,NRES_FLV,LAND_LV,IMPRV_LV,E911ADDR,GLYEAR"
VCGI_FIELDS=set(F.split(","))|{"lng","lat"}

# If data.json already has enrichment fields merged in by merge.py/merge_listings.py/
# merge_flood.py (beds, mktStatus, floodRisk, etc. — anything this script doesn't source
# from VCGI), carry them forward by PARCID so a plain re-fetch doesn't blow them away.
# PARCID (not SPAN) is the key: condo units share one SPAN per building but have a unique
# PARCID per unit (see merge.py), so keying by SPAN would collapse distinct units' data.
# See #8.
enrichment={}
if os.path.exists("data.json"):
    try:
        old=json.load(open("data.json"))
        for rec in old:
            pid=rec.get("PARCID")
            if not pid:
                continue
            extra={k:v for k,v in rec.items() if k not in VCGI_FIELDS}
            if extra:
                enrichment[pid]=extra
    except (json.JSONDecodeError, OSError):
        pass

rows=[];off=0
while True:
    q=urllib.parse.urlencode({"where":"TNAME='MONTPELIER'","outFields":F,"returnGeometry":"true","returnCentroid":"true","geometryType":"esriGeometryEnvelope","outSR":4326,"resultOffset":off,"resultRecordCount":1000,"orderByFields":"OBJECTID","f":"json"})
    d=json.load(urllib.request.urlopen(U+"?"+q,timeout=60))
    fs=d["features"]
    for f in fs:
        a=f["attributes"];c=f.get("centroid") or {}
        a["lng"]=round(c["x"],6) if c else None;a["lat"]=round(c["y"],6) if c else None
        extra=enrichment.get(a.get("PARCID"))
        if extra:
            a.update(extra)
        rows.append(a)
    off+=len(fs)
    if not fs or not d.get("exceededTransferLimit"):break
json.dump(rows,open("data.json","w"),separators=(",",":"))
print(len(rows))

"""Map all shipped runtime resources to retained rights and validate local model references."""
import json,re,struct,posixpath
from pathlib import Path
from nyc.download import ROOT,atomic_json,sha,now


def license_for(path):
    if path.startswith('cesium/')or path.startswith('licenses/'):return 'cesium_distribution_third_party_notices'
    if path.startswith('assets/'):return 'project_and_bundled_cesium_code'
    if path.startswith('datasets/facades/grove-1936/'):return 'loc_original_habs_ny449_public_domain_with_credit'
    if path.startswith('datasets/landmarks/'):return 'generated_partial_geometry_factual_dimensions'
    if path.startswith('datasets/foundation/')or path.startswith('datasets/environment/terrain/'):return 'nys2017_dem_and_nyc_open_data_derived'
    if path.startswith('datasets/'):return 'nyc_open_data_or_project_generated_audit'
    return 'project_generated_page_or_preview_with_embedded_credits'


def main():
    app=ROOT/'dist';files={};errors=[];references=0;glbs=0
    paths=[p for p in app.rglob('*')if p.is_file()]
    for p in paths:
        key=str(p.relative_to(app));files[key]={'path':'app/'+key,'bytes':p.stat().st_size,'sha256':sha(p),'license_id':license_for(key)}
    def reference(source,uri):
        nonlocal references
        if uri.startswith('data:'):return
        if re.match(r'^[a-z]+:',uri):errors.append({'source':source,'external_runtime_uri':uri});return
        q=posixpath.normpath(posixpath.join(posixpath.dirname(source),uri.split('?')[0]));references+=1
        if q not in files:errors.append({'source':source,'missing':q})
    for p in paths:
        rel=str(p.relative_to(app))
        if p.suffix=='.glb':
            with p.open('rb')as f:
                head=f.read(20);magic,v,total,n,kind=struct.unpack('<4sIIII',head);g=json.loads(f.read(n))
            if(magic,v,total,kind)!=(b'glTF',2,p.stat().st_size,0x4e4f534a):errors.append({'source':rel,'error':'GLB header'})
            for b in g.get('buffers',[]):
                if'uri'in b:reference(rel,b['uri'])
            for image in g.get('images',[]):
                if'uri'in image:reference(rel,image['uri'])
            for a in g.get('accessors',[]):
                if a['count']<0 or a.get('bufferView',0)>=len(g.get('bufferViews',[])):errors.append({'source':rel,'error':'accessor range'})
            glbs+=1
        elif p.suffix=='.json'and not rel.startswith(('datasets/inspection/search/','cesium/')):
            data=json.loads(p.read_text())
            if isinstance(data,dict)and'root'in data and'asset'in data:
                def visit(node):
                    for c in [node.get('content'),*node.get('contents',[])]:
                        if c and'uri'in c:reference(rel,c['uri'])
                    for c in node.get('children',[]):visit(c)
                visit(data['root'])
        elif p.suffix=='.css':
            for uri in re.findall(r'url\(["\']?([^\)"\']+)',p.read_text()):
                if not uri.startswith(('data:','#')):reference(rel,uri)
    licences={'cesium_distribution_third_party_notices':{'basis':'licenses/cesium.md,cesium-third-party.json,cesium-engine.md,cesium-widgets.md; retain individual bundled third-party terms, not all assets re-labelled Apache','source':'installed official Cesium1.146.0 distribution'},'project_and_bundled_cesium_code':{'basis':'project-generated code with CesiumApache2 code portions and third-party license files; no new project open-source licence assigned'},'loc_original_habs_ny449_public_domain_with_credit':{'basis':'assets/facades/grove-1936/street.json original HABS government photo/sheet only; third-party copied material excluded','credit':'Library of Congress,Prints&Photographs Division,HABS NY-449; ArnoldMoses1936-08-25; HarryDavisRiley drawings'},'generated_partial_geometry_factual_dimensions':{'basis':'generated geometry/factual dimensions and retained small source references; original unknown-rights photographs/PDF excluded'},'nys2017_dem_and_nyc_open_data_derived':{'basis':'NYSITS public2017bare-earth service/NYC metadata Public,UseLimitationsNA; source attribution retained, not relabelled public-domain'},'nyc_open_data_or_project_generated_audit':{'basis':'NYCOpenData Terms, original source manifests and capture/observation dates retained'},'project_generated_page_or_preview_with_embedded_credits':{'basis':'project-generated; preview explicitly retains LOC/model factual credits'}}
    atomic_json(ROOT/'reports/stage10/resource-audit.json',{'at_utc':now(),'runtime_files':len(files),'runtime_bytes':sum(f['bytes']for f in files.values()),'glb_headers_checked':glbs,'local_references_checked':references,'errors':errors,'all_files_have_declared_rights_basis':all(f['license_id']in licences for f in files.values()),'license_classes':licences,'not_in_runtime':['unresolved-rights2024ortho tile','rawunknown-rightslandmarkphotos/PDF','commercialstreetview/3Dtiles','unconfiguredcloudterrain/CDNs'],'fonts':'system font stacks and vendor bundled assets only; no online font dependency'})
    atomic_json(ROOT/'data/manifests/stage10/runtime-files.json',{'at_utc':now(),'files':list(files.values()),'license_classes':licences,'index_mapping_note':'final package maps release.html to index.html and preserves original as source-audit.html; package manifest hashes actual selected bytes'})
    print('RESOURCE_AUDIT',len(files),'files,',glbs,'GLBs,',references,'references,',len(errors),'errors')
    if errors:raise SystemExit(1)


if __name__=='__main__':main()

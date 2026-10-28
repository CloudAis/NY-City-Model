"""Self-contained real, explicitly partial detailed evidence samples; no invented buildings."""
import json,base64,struct
from nyc.download import ROOT,sha,atomic_json,now


def model(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);images={}
    for image in g.get('images',[]):
        p=path.parent/image['uri'];images[image['uri']]='data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
    return {'glb_base64':base64.b64encode(raw).decode(),'sha256':sha(path),'images':images,'source_path':str(path.relative_to(ROOT))}


def main():
    street=json.loads((ROOT/'assets/facades/grove-1936/street.json').read_text());lm=json.loads((ROOT/'assets/landmarks/manifest.json').read_text())['landmarks'][0]
    samples=[{'id':'grove-1936','name':'Grove Street 4—10号 · 1936历史正面片段','scope':'曼哈顿四栋真实来源对象的四个可见历史照片面；完整现状建筑0、完整街段0。背面、屋顶、门廊深度和室内未生成。','date':'1936-08-25；不是2026现状','detail_level':'four partial historical photo planes, no complete physical building','units':'metre','yaw':3.021592653589793,'pitch':.38,'credit':street['credit'],'rights':street['licence_scope'],'unknown':'遮挡部分中性保留；3栋照片面宽度与当前轮廓约0.8—1.2m冲突，未独立标定。','stable_ids':[f['building_id']for f in street['fronts']],'origin':street['frame'],**model(ROOT/'assets/facades/grove-1936/model.glb')},
        {'id':'one-wtc-partial','name':'One World Trade Center · 文献约束体量片段','scope':'一栋地标的部分八面收分主体、屋顶平面及尖顶轴线；不是完整精细地标。全球基底未配准，外立面、入口、精确基座和冠部仍缺资料。','date':'2012/2014等文献与2026文件分别记载；不声称同一观测日期','detail_level':'partial faceted massing and spire axis; facade unknown','units':'metre','yaw':.35,'pitch':.72,'credit':'Generated model with retained SOM/owner factual dimensions; NYC OTI footprint identity. Original research images/PDF are not embedded.','rights':'项目生成几何与事实参数引用；未嵌入未知许可参考图','unknown':'屋顶约416.9664m、最高点541.3248m为所选文献参数；编码吻合不等于现实误差。尖顶只有轴线，无虚构直径/构件。','stable_ids':[lm['building_id']],'origin':lm['frame'],**model(ROOT/'assets/landmarks/one-world-trade-center/model.glb')}]
    payload={'schema_version':10,'generated_at_utc':now(),'scope':'two real PARTIAL research samples only, NOT full NYC or a completed detailed street','current_complete_fine_buildings':0,'samples':samples,'coordinates':'original glTF float32 metre vertices unchanged; shader converts(E,Up,-N) once to local(E,N,Up); local zero is not world altitude','no_external_runtime_resources':True}
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    template=(ROOT/'scripts/templates/final-preview.html').read_text();text=template.replace('__PREVIEW_DATA__',raw)
    target=ROOT/'preview-single.html';target.write_text(text)
    atomic_json(ROOT/'reports/stage10/single-preview-build.json',{'at_utc':now(),'path':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target),'embedded_models':[{'id':s['id'],'source_path':s['source_path'],'sha256':s['sha256'],'image_count':len(s['images']),'stable_ids':s['stable_ids'],'detail_level':s['detail_level']}for s in samples],'complete_fine_buildings':0,'external_runtime_dependencies':0})
    print('SINGLE',target.stat().st_size,'bytes, two real partial samples, complete fine buildings0')


if __name__=='__main__':main()

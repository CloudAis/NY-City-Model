"""Append missing dossier files only; never overwrite reviewed user evidence."""
from pathlib import Path
import json
from nyc.download import ROOT,atomic_json
LANDMARKS=[
('one-world-trade-center','One World Trade Center','manhattan'),
('empire-state-building','Empire State Building','manhattan'),
('chrysler-building','Chrysler Building','manhattan'),
('flatiron-building','Flatiron Building','manhattan'),
('woolworth-building','Woolworth Building','manhattan'),
('30-rockefeller-plaza','30 Rockefeller Plaza','manhattan'),
('metlife-building','MetLife Building','manhattan'),
('432-park-avenue','432 Park Avenue','manhattan'),
('111-west-57th-street','111 West 57th Street','manhattan'),
('central-park-tower','Central Park Tower','manhattan'),
('one-vanderbilt','One Vanderbilt','manhattan'),
('30-hudson-yards','30 Hudson Yards','manhattan'),
('10-hudson-yards','10 Hudson Yards','manhattan'),
('56-leonard-street','56 Leonard Street','manhattan'),
('un-secretariat','United Nations Secretariat Building','manhattan'),
('grand-central-terminal','Grand Central Terminal','manhattan'),
('nypl-schwarzman','Stephen A. Schwarzman Building','manhattan'),
('st-patricks-cathedral',"St. Patrick’s Cathedral",'manhattan'),
('guggenheim-museum','Solomon R. Guggenheim Museum','manhattan'),
('metropolitan-museum','Metropolitan Museum of Art','manhattan'),
('brooklyn-tower','Brooklyn Tower','brooklyn'),
('1-hanson-place','1 Hanson Place','brooklyn'),
('brooklyn-museum','Brooklyn Museum','brooklyn'),
('twa-flight-center','TWA Flight Center','queens'),
('citi-field','Citi Field','queens'),
('yankee-stadium','Yankee Stadium','bronx'),
('bronx-county-courthouse','Bronx County Courthouse','bronx'),
('staten-island-borough-hall','Staten Island Borough Hall','staten-island'),
('st-george-theatre','St. George Theatre','staten-island')]
def main():
 for slug,name,borough in LANDMARKS:
  p=ROOT/'landmarks'/slug;p.mkdir(parents=True,exist_ok=True)
  files={
   'dossier.json':{'schema_version':1,'slug':slug,'name':name,'borough':borough,'address':None,'stable_building_id':None,'bin':None,'longitude_latitude_degrees':None,'target_date':'2026-10-28','target_date_basis':'requested current stage reference; NOT a claim that all observations are current','source_observation_date':None,'statuses':{'research':'queued','massing':'not_started','facade':'not_started','validation':'not_started'},'model':None,'coordinate_contract':'../../docs/COORDINATES.md; model local metre axes E,Up,-N','world_base_datum_status':'unresolved; no orthometric/ellipsoid substitution'},
   'references.json':{'sources':[],'views':{k:{'reference':None,'capture_date':None,'calibrated':False,'status':'not_acquired'}for k in['north','east','south','west','high','street']}},
   'dimensions.json':{'parameters':[],'rule':'Each value needs source, unit, status, observation date and uncertainty; height/body/roof/spire/antenna kept separate.'},
   'components.json':{'components':[],'missing':['base','podium','setbacks','tower','crown','spire_or_antenna','entrance','facade_grid'],'no_generic_silhouette':True},
   'materials.json':{'materials':[],'rule':'No photo texture redistribution without licence; display colors are not measured albedo.'},
   'validation.json':{'research_complete':False,'massing_complete':False,'facade_complete':False,'validation_complete':False,'checks':[],'dimensions_errors':[],'camera_calibration':None,'pixel_error_is_dimension_error':False}
  }
  for name_,data in files.items():
   if not(p/name_).exists():atomic_json(p/name_,data)
  if not(p/'README.md').exists():(p/'README.md').write_text(f'# {name}\n\n本目录为独立研究档案，不等于模型完成。当前状态见dossier.json；尺寸、组件、材料、参考方向与验证分开保存。未知项保留null，不按名单数量计入精细模型。\n')
  (p/'models').mkdir(exist_ok=True);(p/'models/.gitkeep').touch(exist_ok=True)
 atomic_json(ROOT/'landmarks/queue.json',{'schema_version':1,'requested_landmarks':len(LANDMARKS),'research_list_is_not_model_count':True,'landmarks':[{'slug':s,'name':n,'borough':b,'dossier':f'{s}/dossier.json'}for s,n,b in LANDMARKS]})
 print('DOSSIER_DIRECTORIES',len(LANDMARKS))
if __name__=='__main__':main()

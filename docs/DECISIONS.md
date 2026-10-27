# 决策记录

- D001 2026-10-27：新纽约工程与Tinnis并列，旧资产为虚构游戏，无地理可复用性，不伪装纽约。
- D002：采用用户指定Cesium路线，离线资源本地复制，禁用默认ion、地形和影像。
- D003：优先测绘轮廓线与证据展示，不将有相对高度的平面轮廓擅自变成真实屋顶、立面或默认盒楼。
- D004：源3857与来源2263分开；标准32118米，ENU局部GLB，float64来源保留。
- D005：以DOITT_ID建身份，BIN/BBL作为多对多关系线索；PLUTO是地块级，不传播为楼级真值。
- D006：时间分别保存page_modified/data_published/observation/downloaded；动态API非事务快照，记录两端edit与ID集。

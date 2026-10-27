# 坐标与单位

官方轮廓服务实际发布SR为EPSG:3857（原始测绘来源EPSG:2263 / NAD83纽约长岛US survey foot）；以每个响应spatialReference为准，不能按源测绘CRS误读服务坐标。raw原字节保持；规范平面为EPSG:32118（NAD83纽约长岛米），不可用Web Mercator面积或长度当真实米制面积/长度。

US survey foot=1200/3937m，用于2263水平坐标。HEIGHT_ROOF元数据仅称feet，垂直换算采用0.3048m/ft并标记该惯例与US survey foot未明确差异；不伪称毫米准确。HEIGHT_ROOF是相对屋顶高度，不减GROUND_ELEVATION。后者为最低地面高程，可能合法为负；现代来源通常NAVD88，但单记录缺少明确垂直基准时保留未知限定。

**阶段3取代上述暂算用法**：0.3048仅保留在阶段2legacy记录，不能作为已解决的canonical高度。新的注册表保留原始feet值；foot种类未明确时`value_m=null`、阻止高程相加或世界落位。US survey foot与international foot在1,000,000ft处相差约0.609601m，不能互换。

经纬度/标准平面以float64保留；ECEF EPSG:4978，Cesium tileset.transform为ENU到ECEF，GLB顶点是局部float32米。glTF Y-up写成(East,Up,-North)，3D Tiles默认Y-up转Z-up后成为ENU。显示轮廓暂以WGS84椭球高0作为可视参考，不是实际地面，不把NAVD88直接当椭球高。

投影变换需记录pyproj operation/accuracy；NAD83到WGS84未取得本地网格时不承诺厘米定位。实际修复/投影误差报告与建模本身的测绘误差分开。

全市米制范围见reports/city-dimensions.json；RTree为粗筛包围框，精确数据float64。GLB局部坐标按500m网格处理；真实顶点偏离原点215m/315m的测试恢复ECEF偏差<1mm，只证明数值管线，不是测绘精度。可视轮廓增加0.25m防闪烁并明确标注。

MN01 .3dm实测文档UnitSystem.Feet，OTI元数据为EPSG:2263/US survey foot。百万英尺量级坐标不能忽略foot差异，必须以控制点和技术说明核对；当前未发布该模型变换，也未把其Z当椭球高。影像EPSG:3857分辨率是投影米/像素，不是当地地面GSD。

NYS 2017 DEM服务实际SR2263，像元1 US survey foot，高程波段说明明确“Units converted to meters by NYS”。六个导出文件实际CRS32118，轴E,N、单位米；LERC自身不带CRS，使用同请求exportJSON和逐文件GDAL地理参考核对。垂直NAVD88/GEOID12B来自明确服务说明，不从二维CRS或空band unit猜测。实际索引.prj为6539/NAD83(2011)，与服务generic NAD83不一致，故不自动套用格网。

GEOID12B原始文件及SHA已保存；正式EPSG操作与本模块结果一致。正高H和椭球高h满足h=H+N，N随位置变化，不用固定30m之类偏移。转换必须匹配NAD83(2011)参考框架；未解决DEM仍保留NAVD88原值。当前正高检视的Z是H，坐标种类明确为局部投影，不叫ENU或glTF；不能将其矩阵冒用为ECEF。

30个实际来源顶点分布五区，各6个，保存源页、ID、顶点索引和四类误差。`checkpoints.csv`不是实测控制网。街区、跨东河、跨区测地量距及全城切平面误差评估在配准报告。单城市切平面的曲率偏离可达数十/百米；世界仍保留ECEF曲率。100m投影网与椭球测地标尺分别标记，不用Web Mercator平面长度当真实地面距离。

阶段4批量projected_vertices_to_local使用同一正式32118→经纬度→ECEF→每瓦片ENU变换，输入源高精度保留、GLB float32局部米。原点显式椭球高0；严格线为已声明显示参考+0.25m。假设包络的显示相对高度不构成NAVD88→WGS84转换，未知ground_elevation没有被加到HEIGHT_ROOF。跨格对象完整保留，各自矩阵不全城摊平。

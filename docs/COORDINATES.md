# 坐标与单位

官方轮廓服务实际发布SR为EPSG:3857（原始测绘来源EPSG:2263 / NAD83纽约长岛US survey foot）；以每个响应spatialReference为准，不能按源测绘CRS误读服务坐标。raw原字节保持；规范平面为EPSG:32118（NAD83纽约长岛米），不可用Web Mercator面积或长度当真实米制面积/长度。

US survey foot=1200/3937m，用于2263水平坐标。HEIGHT_ROOF元数据仅称feet，垂直换算采用0.3048m/ft并标记该惯例与US survey foot未明确差异；不伪称毫米准确。HEIGHT_ROOF是相对屋顶高度，不减GROUND_ELEVATION。后者为最低地面高程，可能合法为负；现代来源通常NAVD88，但单记录缺少明确垂直基准时保留未知限定。

经纬度/标准平面以float64保留；ECEF EPSG:4978，Cesium tileset.transform为ENU到ECEF，GLB顶点是局部float32米。glTF Y-up写成(East,Up,-North)，3D Tiles默认Y-up转Z-up后成为ENU。显示轮廓暂以WGS84椭球高0作为可视参考，不是实际地面，不把NAVD88直接当椭球高。

投影变换需记录pyproj operation/accuracy；NAD83到WGS84未取得本地网格时不承诺厘米定位。实际修复/投影误差报告与建模本身的测绘误差分开。

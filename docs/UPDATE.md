# 增量更新、历史与回退

更新范围可为`building`、`tile`、`borough`。单栋必须重新发布包含全部邻楼的完整owner瓦片；跨瓦片归属保持原规则（500m格、来源包围盒中心、完整对象归属、不裁切重复）。主体、属性、逐部件映射、tileset和总目录是相关输入，一起验证。新旧日期、选择依据与原始raw另存，补丁不能提升未知证据等级。

`delivery/update-local.py`只接受`app/datasets/`下文件，拒绝路径越界、重复文件、旧SHA不符、新SHA/大小不符、已应用ID、未声明载荷、丢稳定ID和不完整owner结果。它检查实际GLB feature_ids/JSON objects。SHA用于字节完整性，**不是发布者数字签名**；不要应用不可信补丁。

## 补丁格式

ZIP根目录`patch.json`，其他成员为以下完整替换文件。所有文件在写入前完整校验；`old_sha256:null`只用于不存在的新文件。示意字段，不是伪造的纽约资源：

```json
{
  "id":"unique-version-id",
  "scope":"building",
  "source_version":"retained-real-capture-id",
  "provenance":"source manifest path, dates, processing revision, choice reasons",
  "stable_ids":["nyc:footprints:doitt:1114961"],
  "files":[{"path":"app/datasets/...","old_sha256":"actual previous SHA","sha256":"actual new SHA","bytes":123}]
}
```

先Ctrl+C停止服务器，再运行：

```bash
python3 nyc-local/update-local.py --root nyc-local --apply actual-patch.zip
python3 nyc-local/update-local.py --root nyc-local --rollback unique-version-id
```

备份保存在`.updates/{id}/before`，包括原始交付manifest，journal记录prepared/applying/committed/rolled_back；回退按逆序。正常更新保存来源历史，更新交付文件SHA和总字节数。重复应用不会重写。失败会尝试还原已写文件；进程被强杀后，可按prepared/applying journal明确回退。多文件不是并发服务器事务，不能边浏览边更新。回退后该ID历史保留，下一次用新ID。

## 已执行与边界

本轮使用真实owner属性文件，三种scope分别实际应用及回退，恢复原文件字节和原manifest；模拟遗漏真实邻楼被拒绝，未修改live文件。另实际重建单栋、完整20对象瓦片及全曼哈顿索引，见`reports/stage10/incremental-rebuild.json`和`update-tests.log`。

工具目前保守**不支持直接删除既有稳定ID**；拆除需保留该ID的历史/状态或先人工审核新发布规则。它不能自动判定现实拆除、解决来源许可或确认新模型现实准确性。尚无真实新采集版本可用来证明跨年代更新匹配完成。

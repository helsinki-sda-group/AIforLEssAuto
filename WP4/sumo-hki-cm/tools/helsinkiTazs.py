# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    helsinkiTazs.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------
REDUCED_AREA_TAZS = set([
    "po_101",
    "po_102",
    "po_103",
    "po_104",
    "po_105",
    "po_111",
    "po_112",
    "po_113",
    "po_114",
    "po_115",
    "po_116",
    "po_117",
    "po_118",
    "po_131",
    "po_132",
    "po_133",
    "po_141",
    "po_142",
    "po_143",
    "po_151",
    "po_152",
    "po_153",
    "po_154",
    "po_161",
    "po_162",
    "po_171",
    "po_172",
    "po_173",
    "po_174",
    "po_175",
    "po_181",
    "po_182",
    "po_183",
    "po_191",
    "po_192",
    "po_193",
    "po_194",
    "po_195",
    "po_196",
    "po_197",
    "po_201",
    "po_202",
    "po_203",
    "po_211",
    "po_212",
    "po_213",
    "po_214",
    "po_215",
    "po_221",
    "po_222",
    "po_223",
    "po_224",
    "po_225",
    "po_231",
    "po_232",
    "po_233",
    "po_234",
    "po_235",
    "po_236",
    "po_241",
    "po_242",
    "po_243",
    "po_244",
    "po_251",
    "po_252",
    "po_253",
    "po_254",
    "po_255",
    "po_260",
    "po_271",
    "po_272",
    "po_281",
    "po_282",
    "po_291",
    "po_292",
    "po_293",
    "po_294",
    "po_301",
    "po_302",
    "po_303",
    "po_304",
    "po_305",
    "po_306",
    "po_307",
    "po_308",
    "po_321",
    "po_322",
    "po_323",
    "po_331",
    "po_332",
    "po_333",
    "po_341",
    "po_342",
    "po_343",
    "po_344",
    "po_345",
    "po_346",
    "po_351",
    "po_352",
    "po_353",
    "po_354",
    "po_355",
    "po_356",
    "po_361",
    "po_362",
    "po_363",
    "po_364",
    "po_365",
    "po_366",
    "po_367",
    "po_368",
    "po_369",
    "po_381",
    "po_382",
    "po_383",
    "po_384",
    "po_385",
    "po_386",
    "po_1001",
    "po_1002",
    "po_1003",
    "po_1004",
    "po_1005",
    "po_1011",
    "po_1012",
    "po_1013",
    "po_1014",
    "po_1021",
    "po_1022",
    "po_1023",
    "po_1024",
    "po_1025",
    "po_1026",
    "po_1027",
    "po_1031",
    "po_1032",
    "po_1033",
    "po_1034",
    "po_1035",
    "po_1041",
    "po_1042",
    "po_1043",
    "po_1044",
    "po_1045",
    "po_1046",
    "po_1047",
    "po_1051",
    "po_1052",
    "po_1053",
    "po_1054",
    "po_1055",
    "po_1056",
    "po_1061",
    "po_1062",
    "po_1063",
    "po_1064",
    "po_1065",
    "po_1066",
    "po_1067",
    "po_1068",
    "po_1069",
    "po_1071",
    "po_1081",
    "po_1082",
    "po_1083",
    "po_1084",
    "po_1085",
    "po_1091",
    "po_1092",
    "po_1093",
    "po_1094",
    "po_1101",
    "po_1102",
    "po_1103",
    "po_1104",
    "po_1111",
    "po_1112",
    "po_1113",
    "po_1114",
    "po_1115",
    "po_1116",
    "po_1121",
    "po_1122",
    "po_1123",
    "po_1124",
    "po_1125",
    "po_1126",
    "po_1127",
    "po_1128",
    "po_1141",
    "po_1142",
    "po_1143",
    "po_1144",
    "po_1145",
    "po_1146",
    "po_1147",
    "po_1148",
    "po_1149",
    "po_1151",
    "po_1161",
    "po_1162",
    "po_1163",
    "po_1164",
    "po_1171",
    "po_1172",
    "po_1173",
    "po_1174",
    "po_1175",
    "po_1181",
    "po_1182",
    "po_1183",
    "po_1184",
    "po_1185",
    "po_1191",
    "po_1192",
    "po_1193",
    "po_1201",
    "po_1202",
    "po_1203",
    "po_1204",
    "po_1205",
    "po_1206",
    "po_1211",
    "po_1212",
    "po_1213",
    "po_1214",
    "po_1215",
    "po_1221",
    "po_1222",
    "po_1223",
    "po_1224",
    "po_1225",
    "po_1226",
    "po_1227",
    "po_1228",
    "po_1241",
    "po_1242",
    "po_1243",
    "po_1244",
    "po_1245",
    "po_1246",
    "po_1247",
    "po_1248",
    "po_1261",
    "po_1262",
    "po_1263",
    "po_1271",
    "po_1272",
    "po_1273",
    "po_1274",
    "po_1275",
    "po_1281",
    "po_1282",
    "po_1283",
    "po_1284",
    "po_1285",
    "po_1286",
    "po_1287",
    "po_1291",
    "po_1292",
    "po_1293",
    "po_1294",
    "po_1301",
    "po_1302",
    "po_1303",
    "po_1304",
    "po_1311",
    "po_1312",
    "po_1313",
    "po_1314",
    "po_1321",
    "po_1322",
    "po_1331",
    "po_1332",
    "po_1333",
    "po_1334",
    "po_1335",
    "po_1336",
    "po_1337",
    "po_1340",
    "po_1351",
    "po_1352",
    "po_1353",
    "po_1354",
    "po_1355",
    "po_1356",
    "po_1357",
    "po_1358",
    "po_1371",
    "po_1372",
    "po_1373",
    "po_1374",
    "po_1375",
    "po_1381",
    "po_1382",
    "po_1383",
    "po_1384",
    "po_1391",
    "po_1392",
    "po_1393",
    "po_1394",
    "po_1401",
    "po_1402",
    "po_1403",
    "po_1404",
    "po_1405",
    "po_1411",
    "po_1412",
    "po_1421",
    "po_1422",
    "po_1423",
    "po_1424",
    "po_1431",
    "po_1432",
    "po_1433",
    "po_1434",
    "po_1435",
    "po_1436",
    "po_1441",
    "po_1442",
    "po_1443",
    "po_1444",
    "po_1445",
    "po_1451",
    "po_1452",
    "po_1453",
    "po_1454",
    "po_1455",
    "po_1461",
    "po_1462",
    "po_1463",
    "po_1464",
    "po_1465",
    "po_1471",
    "po_1472",
    "po_1473",
    "po_1474",
    "po_1475",
    "po_1476",
    "po_1477",
    "po_1478",
    "po_1491",
    "po_1492",
    "po_1493",
    "po_1494",
    "po_1495",
    "po_1496",
    "po_1497",
    "po_1498",
    "po_1499",
    "po_1511",
    "po_1512",
    "po_1513",
    "po_1514",
    "po_1515",
    "po_1516",
    "po_1520",
    "po_1531",
    "po_1532",
    "po_1541",
    "po_1542",
    "po_1543",
    "po_1544",
    "po_1545",
    "po_1546",
    "po_1547",
    "po_1548",
    "po_1561",
    "po_1562",
    "po_1563",
    "po_1564",
    "po_1565",
    "po_1570",
    "po_1581",
    "po_1582",
    "po_1591",
    "po_1592",
    "po_1593",
    "po_1601",
    "po_1602",
    "po_1603"
])
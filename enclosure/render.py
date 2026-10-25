import trimesh, numpy as np, glob, pickle, os, pyvista as pv
m = pickle.load(open("_meta.pkl", "rb")); OX, OY, HB, KH = m["OX"], m["OY"], m["HB"], m["KAP_H"]
g = trimesh.load("govde.stl"); k = trimesh.load("kapak.stl")
print("watertight", g.is_watertight, k.is_watertight)
gp = g.copy(); gp.apply_translation(-gp.bounds[0] + [17, 8, 0])
kp = k.copy(); kp.apply_translation(-kp.bounds[0] + [17, 8, 0])
gp.apply_translation([0, (256 - (gp.bounds[1][1]-gp.bounds[0][1]))/2 - 8, 0]); kp.apply_translation([0, (256 - (kp.bounds[1][1]-kp.bounds[0][1]))/2 - 8, 0])
R = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
km = k.copy(); km.apply_transform(R); km.apply_translation([0, OY, HB + KH])
P = {os.path.basename(f)[:-4]: trimesh.load(f) for f in glob.glob("parca_modelleri/*.stl")}
renk = {"ESP32": "#7b1fa2", "USB": "#455a64", "PERT": "#2e7d32", "TIP": "#111111", "BUCK": "#f9a825", "DC_JAK": "#212121", "DC_fis": "#616161", "VALF_govde": "#c9a227", "SIMDI_VALF_govde": "#c9a227", "SIMDI_VALF_bobin": "#263238", "SIMDI_TAKOZ": "#ff7043", "SIMDI_UZ": "#c9a227", "SIMDI": "#c9a227", "GEL_BVALF_govde": "#b8860b", "GEL_BVALF_bobin": "#1b2a33", "GEL_TVALF_bobin": "#263238", "GEL_SUS": "#9e9e9e", "GEL_PERT": "#2e7d32", "GEL_TIP": "#111111", "GEL": "#c9a227",
        "VALF_bobin": "#263238", "VALF_dis": "#c9a227", "VALF_kablo": "#1e88e5", "RED": "#d4af37", "NIPEL": "#c9a227", "T_": "#c9a227", "SENSOR": "#b0bec5", "HRAKOR": "#90a4ae", "HORTUM": "#1976d2", "BTN": "#43a047", "LCD_kel": "#ff7043", "LCD_kab": "#00acc1", "LCD": "#0d47a1"}
col = lambda a: next((v for kk, v in renk.items() if a.startswith(kk)), "#888888")
def pvm(t): return pv.PolyData(t.vertices, np.hstack([np.full((len(t.faces), 1), 3), t.faces]).ravel())
def kablolar():
    out = []
    for n, (c, pts) in m["KAB"].items():
        out.append((pv.Spline(np.array(pts, float), 60).tube(radius=1.3), c))
    return out
def plot(items, fn, cam, title, zoom=1.2, labels=None, tubes=(), legend=None):
    p = pv.Plotter(off_screen=True, window_size=(1600, 1100)); p.set_background("white")
    for mesh, c in items:
        p.add_mesh(pvm(mesh), color=c, smooth_shading=True, split_sharp_edges=True, specular=0.3)
        p.add_mesh(pvm(mesh).extract_feature_edges(feature_angle=40, boundary_edges=False, non_manifold_edges=False, manifold_edges=False), color="#222222", line_width=1)
    for t, c in tubes: p.add_mesh(t, color=c, smooth_shading=True)
    if labels:
        p.add_point_labels(np.array([l[0] for l in labels]), [l[1] for l in labels], font_size=13, point_size=6, shape_opacity=0.75, always_visible=True)
    if legend: p.add_legend(legend, bcolor="white", size=(0.22, 0.3), loc="lower right")
    p.camera_position = cam; p.camera.zoom(zoom); p.add_text(title, font_size=12, color="black")
    p.enable_anti_aliasing("ssaa"); p.screenshot(fn); p.close()
c = (OX/2, OY/2, (HB + KH)/2)
plot([(g, "#37474f"), (km, "#eceff1")], "izometrik.png", [(OX/2 - 190, OY/2 + 330, HB + 300), c, (0, 0, 1)], f"izometrik - dış {OX:.0f} x {OY:.0f} x {HB+KH:.0f} mm")
plot([(g, "#37474f"), (km, "#eceff1")], "on.png", [(OX/2, OY/2, 750), (OX/2, OY/2, HB), (0, -1, 0)], "ön görünüm", 1.15)
plot([(g, "#37474f"), (km, "#eceff1")], "alt_hortum.png", [(OX/2 + 60, OY + 380, HB/2 + 150), c, (0, 0, 1)], "alt/sağ: Ø31 hortum delikleri, DC jak, havalandırma", 1.2)
etik = {"ESP32": "ESP32", "PERTINAKS": "Pertinaks 1 (TIP102 #1)", "BUCK_5V": "5V buck", "DC_JAK": "DC jak", "T_TAHLIYE": "T (tahliye kolu)", "T_RAKOR": "T (sensör)", "SENSOR": "Sensör", "RED_cikis": "3/4 çıkış", "RED_giris": "3/4 giriş",
  "SIMDI_VALF_bobin": "Küçük valf 2W-025-08 (şişirme, ŞİMDİ)", "SIMDI_UZATMA_80": "1/4 uzatma nipel ~75", "SIMDI_TAPA": "1/4 kör tapa", "SIMDI_TAKOZ": "Valf takozu (ayrı baskı)",
  "GEL_BVALF_govde": "BÜYÜK valf 2W-160-15 (GELECEK)", "GEL_TVALF_govde": "Küçük valf -> TAHLİYE (GELECEK)", "GEL_SUSTURUCU": "1/4 susturucu -> sağ duvar Ø16", "GEL_PERT2": "Pertinaks 2 (TIP102 #2, GPIO26)"}
leg = [[n, cc] for n, (cc, _) in m["KAB"].items()]
for sen, ex_ in (("simdi", "GEL_"), ("gelecek", "SIMDI_")):
    Ps = {a: v for a, v in P.items() if not a.startswith(ex_)}
    lab = [(Ps[a].bounds.mean(0) + [0, 0, 40], t) for a, t in etik.items() if a in Ps]
    ic = [(g, "#cfd8dc")] + [(v, col(a)) for a, v in Ps.items() if not a.startswith(("BTN", "LCD"))]
    plot(ic, f"ic_yerlesim_{sen}.png", [(OX/2, OY/2 + 1, 650), (OX/2, OY/2, 0), (0, -1, 0)], f"iç yerleşim - {'ŞİMDİ (küçük valf şişirme)' if sen=='simdi' else 'GELECEK (büyük valf şişirme + küçük valf tahliye)'}", 1.15, lab, kablolar(), leg)
    plot(ic, f"ic_izometrik_{sen}.png", [(OX/2 - 190, OY/2 + 300, 400), (OX/2, OY/2, 15), (0, 0, 1)], f"iç izometrik - {sen}", 1.2, None, kablolar())
ex = []
for a, v in P.items():
    if a.startswith("GEL_"): continue
    vv = v.copy(); vv.apply_translation([0, 0, 120 if a.startswith(("BTN", "LCD")) else 55]); ex.append((vv, col(a)))
kx = km.copy(); kx.apply_translation([0, 0, 150])
plot([(g, "#37474f"), (kx, "#eceff1")] + ex, "patlatilmis.png", [(OX/2 - 320, OY/2 + 400, 400), (OX/2, OY/2, 100), (0, 0, 1)], "patlatılmış (şimdiki parçalar)", 1.05)

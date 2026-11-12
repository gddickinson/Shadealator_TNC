// Synthetic stream reach: centreline, banks, DEM and vegetation-height rasters. A line-for-line port of
// shadealator/synthetic.py (same formulas, same cell order) so the browser and Python build identical rasters.
// Coordinates in metres, x east, y north; the stream flows south from y = length to y = 0; the left bank (facing
// downstream) is the east side. Parameters come complete from the API (/api/scene_spec defaults), never defaulted here.

export const Z0 = 1480.0;

export function centreX(p, y) {
  return p.meander_amp_m * Math.sin(2 * Math.PI * y / p.meander_wavelength_m);
}

export function lines(p) {
  const n = Math.trunc(p.length_m), half = p.channel_width_m / 2;
  const centre = [], left = [], right = [];
  for (let i = 0; i <= n; i++) {
    const y = i, xc = centreX(p, y);
    centre.push([xc, y]); left.push([xc + half, y]); right.push([xc - half, y]);
  }
  return { centre, left, right };
}

export function extent(p) {
  const c = p.cellsize_m;
  const margin = p.topo_search_m + 10 * c + 20;
  const halfW = p.meander_amp_m + Math.max(p.floodplain_half_m + p.wall_width_m,
    p.channel_width_m / 2 + 9 * p.sample_dist_m) + margin;
  const ncols = 2 * Math.ceil(halfW / c);
  const nrows = Math.ceil((p.length_m + 2 * margin) / c);
  return { x_min: -ncols / 2 * c, y_min: -Math.ceil(margin / c) * c, ncols, nrows };
}

export function ground(p, x, y) {
  const dx = x - centreX(p, y), ad = Math.abs(dx);
  let z = Z0 + p.bed_slope * y;
  z -= p.dip_m * Math.max(0.0, 1 - Math.abs(y - p.length_m / 2) / 30);
  if (ad <= p.channel_width_m / 2) z -= p.incision_m;
  const t = Math.min(Math.max((ad - p.floodplain_half_m) / p.wall_width_m, 0.0), 1.0);
  const h = dx < 0 ? p.wall_west_m : p.wall_east_m;
  return z + h * t * t * (3 - 2 * t);
}

export function coverCm(p, x, y) {
  const dx = x - centreX(p, y);
  const bank = Math.abs(dx) - p.channel_width_m / 2;
  if (bank < 0) return 0;
  const sideOn = dx > 0 ? p.veg_left : p.veg_right;
  const inBand = p.veg_gap_m <= bank && bank < p.veg_gap_m + p.veg_band_m;
  const h = (sideOn && inBand) ? p.veg_height_m : p.low_cover_m;
  return Math.round(h * 100);
}

// A raster: Float64Array in row-major order, row 0 at the north edge (like ESRI grids and the Python FakeRaster).
export function rasters(p) {
  const { x_min, y_min, ncols, nrows } = extent(p);
  const c = p.cellsize_m, y_max = y_min + nrows * c;
  const dem = new Float64Array(nrows * ncols), cov = new Float64Array(nrows * ncols);
  for (let r = 0; r < nrows; r++) {
    const y = y_max - (r + 0.5) * c;
    for (let col = 0; col < ncols; col++) {
      const x = x_min + (col + 0.5) * c;
      dem[r * ncols + col] = ground(p, x, y);
      cov[r * ncols + col] = coverCm(p, x, y);
    }
  }
  const meta = { x_min, y_min, cellsize: c, ncols, nrows, x_max: x_min + ncols * c, y_max };
  return { dem: { ...meta, data: dem }, cover: { ...meta, data: cov } };
}

export const at = (ras, row, col) => ras.data[row * ras.ncols + col];

export interface Pieza {
  descripcion: string;
  cantidad: number;
}

export interface Recorte {
  largo_mm: number | null;
  ancho_mm: number | null;
}

export interface PropuestaExtraccion {
  multiplicidad: number | null;
  espesor_mm: number | null;
  material: string | null;
  largo_mm: number | null;
  ancho_mm: number | null;
  tiempo_ejecucion_estimado: string | null;
  piezas: Pieza[];
  recortes: Recorte[];
  extraccion_incompleta: boolean;
}

export interface ProductoComprometido {
  id: number;
  creado_automaticamente: boolean;
}

export interface OrdenOut {
  id: number;
  codigo_nest: string;
  estado: string;
  producto_comprometido: ProductoComprometido;
  alerta_stock_bajo: boolean;
}

export interface OrdenListado {
  id: number;
  codigo_nest: string;
  estado: string;
  material: string;
  espesor_mm: number;
  largo_mm: number;
  ancho_mm: number;
  multiplicidad: number;
  tiempo_ejecucion_estimado: string;
  created_at: string;
  closed_at: string | null;
}

export interface OrdenDetalle extends OrdenListado {
  piezas: Pieza[];
  recortes: Recorte[];
}

export interface OrdenCerrada {
  id: number;
  estado: string;
  closed_at: string;
}

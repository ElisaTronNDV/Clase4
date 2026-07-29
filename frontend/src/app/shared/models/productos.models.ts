export interface ProductoOut {
  id: number;
  material: string;
  espesor_mm: number;
  largo_mm: number;
  ancho_mm: number;
  stock_fisico: number;
  stock_comprometido: number;
  punto_pedido: number;
  alerta_stock_bajo: boolean;
}

export interface ProductoCreate {
  material: string;
  espesor_mm: number;
  largo_mm: number;
  ancho_mm: number;
  stock_fisico: number;
  punto_pedido: number;
}

export type ProductoUpdate = ProductoCreate;

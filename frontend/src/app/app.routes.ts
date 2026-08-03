import { Routes } from '@angular/router';

import { authGuard } from './auth/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'registro',
    loadComponent: () =>
      import('./auth/registro/registro.component').then((m) => m.RegistroComponent),
  },
  {
    path: 'logout',
    loadComponent: () =>
      import('./auth/logout/logout.component').then((m) => m.LogoutComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/layout/layout.component').then((m) => m.LayoutComponent),
    children: [
      {
        path: 'home',
        loadComponent: () => import('./home/home.component').then((m) => m.HomeComponent),
      },
      {
        path: 'oficina',
        children: [
          { path: '', redirectTo: 'listado', pathMatch: 'full' },
          {
            path: 'subir',
            loadComponent: () =>
              import('./oficina/subir-pdf/subir-pdf.component').then((m) => m.SubirPdfComponent),
          },
          {
            path: 'revisar',
            loadComponent: () =>
              import('./oficina/revisar-orden/revisar-orden.component').then(
                (m) => m.RevisarOrdenComponent
              ),
          },
          {
            path: 'listado',
            loadComponent: () =>
              import('./oficina/listado-ordenes/listado-ordenes.component').then(
                (m) => m.ListadoOrdenesComponent
              ),
          },
          {
            path: 'impresion/:nest',
            loadComponent: () =>
              import('./oficina/orden-impresion/orden-impresion.component').then(
                (m) => m.OrdenImpresionComponent
              ),
          },
        ],
      },
      {
        path: 'taller',
        children: [
          { path: '', redirectTo: 'escanear', pathMatch: 'full' },
          {
            path: 'escanear',
            loadComponent: () =>
              import('./taller/escanear-orden/escanear-orden.component').then(
                (m) => m.EscanearOrdenComponent
              ),
          },
          {
            path: 'cerrar',
            loadComponent: () =>
              import('./taller/cerrar-orden/cerrar-orden.component').then(
                (m) => m.CerrarOrdenComponent
              ),
          },
        ],
      },
      {
        path: 'inventario',
        children: [
          { path: '', redirectTo: 'listado', pathMatch: 'full' },
          {
            path: 'listado',
            loadComponent: () =>
              import('./inventario/listado-productos/listado-productos.component').then(
                (m) => m.ListadoProductosComponent
              ),
          },
          {
            path: 'alta',
            loadComponent: () =>
              import('./inventario/alta-producto/alta-producto.component').then(
                (m) => m.AltaProductoComponent
              ),
          },
          {
            path: 'editar/:id',
            loadComponent: () =>
              import('./inventario/editar-producto/editar-producto.component').then(
                (m) => m.EditarProductoComponent
              ),
          },
        ],
      },
      {
        path: 'configuracion',
        loadComponent: () =>
          import('./configuracion/margen-tolerancia/margen-tolerancia.component').then(
            (m) => m.MargenToleranciaComponent
          ),
      },
    ],
  },
];

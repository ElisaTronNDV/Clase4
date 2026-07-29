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
    path: 'oficina',
    canActivate: [authGuard],
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
        path: 'impresion/:id',
        loadComponent: () =>
          import('./oficina/orden-impresion/orden-impresion.component').then(
            (m) => m.OrdenImpresionComponent
          ),
      },
    ],
  },
  { path: 'taller', canActivate: [authGuard] },
  { path: 'inventario', canActivate: [authGuard] },
  { path: 'configuracion', canActivate: [authGuard] },
];

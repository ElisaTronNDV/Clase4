import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { authInterceptor, TOKEN_STORAGE_KEY } from './auth.interceptor';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    httpClient = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpTesting.verify();
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  });

  it('agrega el header Authorization cuando hay token guardado', () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'token-de-prueba');

    httpClient.get('/api/ordenes').subscribe();

    const req = httpTesting.expectOne('/api/ordenes');
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-de-prueba');
    req.flush({});
  });

  it('no agrega el header cuando no hay token', () => {
    httpClient.get('/api/ordenes').subscribe();

    const req = httpTesting.expectOne('/api/ordenes');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('ante un 401 borra el token y redirige a /login', () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'token-expirado');
    const navigateSpy = spyOn(router, 'navigate');

    httpClient.get('/api/ordenes').subscribe({ error: () => {} });

    const req = httpTesting.expectOne('/api/ordenes');
    req.flush({ detail: 'No autenticado' }, { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });
});

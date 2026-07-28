import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { authGuard } from './auth.guard';
import { AuthTokenService } from './auth-token.service';

describe('authGuard', () => {
  let tokenService: AuthTokenService;
  let router: Router;

  const runGuard = () =>
    TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    tokenService = TestBed.inject(AuthTokenService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('permite el acceso si hay un token guardado', () => {
    tokenService.setToken('token-valido');
    expect(runGuard()).toBeTrue();
  });

  it('bloquea el acceso y redirige a /login si no hay token', () => {
    const navigateSpy = spyOn(router, 'navigate');
    expect(runGuard()).toBeFalse();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });
});

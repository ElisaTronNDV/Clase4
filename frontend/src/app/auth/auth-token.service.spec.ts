import { TestBed } from '@angular/core/testing';

import { AuthTokenService } from './auth-token.service';

describe('AuthTokenService', () => {
  let service: AuthTokenService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthTokenService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('no hay token por defecto', () => {
    expect(service.getToken()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('guarda y lee el token', () => {
    service.setToken('abc123');
    expect(service.getToken()).toBe('abc123');
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('borra el token', () => {
    service.setToken('abc123');
    service.clearToken();
    expect(service.getToken()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
  });
});

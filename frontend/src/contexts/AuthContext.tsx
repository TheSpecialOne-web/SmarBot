import { useAuth0 } from "@auth0/auth0-react";
import * as Sentry from "@sentry/react";
import { AxiosError, AxiosHeaders, InternalAxiosRequestConfig } from "axios";
import { useSnackbar } from "notistack";
import { createContext, ReactNode, useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ERROR } from "@/const";
import { useLaunchDarkly } from "@/hooks/useLaunchDarkly";
import { administratorInstance } from "@/libs/administrator/mutator";
import { instance } from "@/libs/mutator";
import { useGetUserInfo } from "@/orval/backend-api";
import { UserInfo } from "@/orval/models/backend-api";
import { useEffectAsync } from "@/utils/useEffectAsync";

type AuthContextType = {
  accessToken: string;
  userInfo: UserInfo;
  fetchUserInfo: () => void;
};

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthContextProvider = ({ children }: { children: ReactNode }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isTenantSet, setIsTenantSet] = useState<boolean>(false);

  const navigate = useNavigate();
  const { isLoading, getAccessTokenSilently, logout } = useAuth0();
  const { enqueueSnackbar } = useSnackbar();
  const { updateTenantContext } = useLaunchDarkly();

  const fetchToken = useCallback(async () => {
    if (isLoading) return;
    try {
      const token = await getAccessTokenSilently();
      if (!token) {
        throw new Error("Failed to get access token");
      }
      setAccessToken(token);
      return token;
    } catch (e) {
      enqueueSnackbar("アクセストークンの取得に失敗しました。", {
        variant: "error",
        preventDuplicate: true,
      });
      setAccessToken(null);
      navigate("/");
    }
  }, [enqueueSnackbar, getAccessTokenSilently, isLoading, navigate]);

  const onLogout = (reason: ERROR) => {
    const returnToUrl = `${window.location.origin}?logout_reason=${reason}`;
    logout({ logoutParams: { returnTo: returnToUrl } });
  };

  const handleResponseError = (error: AxiosError) => {
    if (!error.response) {
      return Promise.reject(error);
    }

    const status = error.response.status;

    switch (status) {
      case 401:
        onLogout(ERROR.UNAUTHORIZED);
        break;
      case 403:
        onLogout(ERROR.FORBIDDEN);
        break;
      default:
        break;
    }

    return Promise.reject(error);
  };
  const { data: userInfo, mutate: fetchUserInfo } = useGetUserInfo({
    swr: {
      enabled: Boolean(accessToken),
    },
  });

  const addXTenantIdHeader = useCallback((token: string, tenantId: number) => {
    const headers = {
      Authorization: `Bearer ${token}`,
      "X-Tenant-Id": tenantId.toString(),
    };
    const interceptorId = instance.interceptors.request.use(
      (config): InternalAxiosRequestConfig => ({
        ...config,
        headers: new AxiosHeaders({
          ...config.headers,
          ...headers,
        }),
      }),
    );
    setIsTenantSet(true);
    return () => {
      instance.interceptors.request.eject(interceptorId);
    };
  }, []);

  useEffectAsync(async () => {
    if (accessToken && userInfo) {
      updateTenantContext(userInfo.tenant);

      Sentry.setUser({
        id: userInfo.id,
        tenant: userInfo.tenant.name,
      });

      return addXTenantIdHeader(accessToken, userInfo.tenant.id);
    }

    const token = await fetchToken();
    if (!token) return;
    const headers = {
      Authorization: `Bearer ${token}`,
    };

    const interceptorId = instance.interceptors.request.use(
      (config): InternalAxiosRequestConfig => ({
        ...config,
        headers: new AxiosHeaders({
          ...config.headers,
          ...headers,
        }),
      }),
    );

    const administratorInterceptorId = administratorInstance.interceptors.request.use(
      (config): InternalAxiosRequestConfig => ({
        ...config,
        headers: new AxiosHeaders({
          ...config.headers,
          ...headers,
        }),
      }),
    );

    const responseInterceptorId = instance.interceptors.response.use(
      response => response,
      error => handleResponseError(error),
    );

    const adminResponseInterceptorId = administratorInstance.interceptors.response.use(
      response => response,
      error => handleResponseError(error),
    );

    return () => {
      instance.interceptors.request.eject(interceptorId);
      administratorInstance.interceptors.request.eject(administratorInterceptorId);
      instance.interceptors.response.eject(responseInterceptorId);
      administratorInstance.interceptors.response.eject(adminResponseInterceptorId);
    };
  }, [accessToken, userInfo]);

  if (!accessToken || !userInfo || !isTenantSet) {
    return null;
  }

  const contextValue: AuthContextType = {
    accessToken,
    userInfo,
    fetchUserInfo,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

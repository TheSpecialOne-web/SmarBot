export type ExternalDataConnectionInfo<K> = {
  key: K;
  label: string;
  description: string;
};

export type SharepointConnectionKey = "client_id" | "client_secret" | "tenant_id";
export const sharepointConnectionsInfo: readonly ExternalDataConnectionInfo<SharepointConnectionKey>[] =
  [
    {
      key: "client_id",
      label: "Application (client) ID",
      description: 'Azureの"アプリの登録"で作成したアプリのクライアントID',
    },
    {
      key: "client_secret",
      label: "Client Secret",
      description: 'Azureの"アプリの登録"の"証明書とシークレット"から取得したシークレット',
    },
    {
      key: "tenant_id",
      label: "Tenant ID",
      description: "AzureのテナントID",
    },
  ] as const;

import "./libs/sentry";

import { withLDProvider } from "launchdarkly-react-client-sdk";
import { HashRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AuthContextProvider } from "./contexts/AuthContext";
import { BotContextProvider } from "./contexts/BotContext";
import { ConversationContextProvider } from "./contexts/ConversationContext";
import { EmbedContextProvider } from "./contexts/EmbedContext";
import { AdministratorLayout } from "./layouts/AdministratorLayout";
import { ChatLayout } from "./layouts/ChatLayout";
import { GroupManagementLayout } from "./layouts/GroupManagementLayout";
import { LoginLayout } from "./layouts/LoginLayout";
import { ManagementLayout } from "./layouts/ManagementLayout";
import { RouterAdministratorGuard } from "./modules/administrator/RouterAdministratorGuard";
import { AdministratorsPage } from "./pages/administrator/administrators";
import { AssistantTemplatesPage } from "./pages/administrator/assistant-templates";
import { AssistantTemplateDetailPage } from "./pages/administrator/assistant-templates/[assistantTemplateId]";
import { AssistantTemplateEditPage } from "./pages/administrator/assistant-templates/[assistantTemplateId]/edit";
import { AssistantTemplateCreatePage } from "./pages/administrator/assistant-templates/create";
import { AdministratorBot } from "./pages/administrator/bots";
import Admin from "./pages/administrator/index";
import { NotificationsPage } from "./pages/administrator/notifications";
import { ArchivedNotificationsPage } from "./pages/administrator/notifications/archived";
import { TenantsPage } from "./pages/administrator/tenants";
import { TenantDetailPage } from "./pages/administrator/tenants/[tenantId]";
import { EmbedPage } from "./pages/embed";
import Login from "./pages/login";
import { AssistantsPage } from "./pages/main/assistants";
import { AssistantDetailPage } from "./pages/main/assistants/[assistantId]";
import { AssistantsEditPage } from "./pages/main/assistants/[assistantId]/edit";
import { ArchivedAssistantsPage } from "./pages/main/assistants/archived";
import { AssistantsCreatePage } from "./pages/main/assistants/create";
import { CreateAssistantFromTemplatesPage } from "./pages/main/assistants/create-from-template";
import { BotsSearchPage } from "./pages/main/bots/search";
import { ChatPage } from "./pages/main/chat";
import { GroupsPage } from "./pages/main/groups";
import { GroupAssistantsPage } from "./pages/main/groups/[groupId]/assistants";
import { GroupArchivedAssistantsPage } from "./pages/main/groups/[groupId]/assistants/archived";
import { GroupUsersPage } from "./pages/main/groups/[groupId]/users";
import { AddUsersToGroupPage } from "./pages/main/groups/[groupId]/users/add-users";
import { TenantSettingsPage } from "./pages/main/tenant-settings";
import { TenantUsageDashboardPage } from "./pages/main/usage";
import { UsersPage } from "./pages/main/users";
import { UserDetailPage } from "./pages/main/users/[userId]";
import NoPage from "./pages/NoPage";

const Pages = () => {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<LoginLayout />}>
          <Route index element={<Login />} />
        </Route>
        <Route
          element={
            <AuthContextProvider>
              <Outlet />
            </AuthContextProvider>
          }
        >
          {/* user */}
          <Route path="/main">
            {/* chat */}
            <Route
              element={
                <BotContextProvider>
                  <ConversationContextProvider>
                    <ChatLayout />
                  </ConversationContextProvider>
                </BotContextProvider>
              }
            >
              <Route index element={<ChatPage />} />
              <Route path="chat">
                <Route index element={<ChatPage />} />
                <Route path=":conversationId" element={<ChatPage />} />
              </Route>
              <Route path="bots/search" element={<BotsSearchPage />} />
              {/* 後方互換用リダイレクト */}
              <Route path="chat-search" element={<Navigate to="/main/chat" />} />
              <Route path="chat-gpt" element={<Navigate to="/main/chat" />} />
              <Route path="*" element={<NoPage />} />
            </Route>
            {/* management */}
            <Route element={<ManagementLayout />}>
              <Route path="assistants">
                <Route index element={<AssistantsPage />} />
                <Route path=":assistantId" element={<AssistantDetailPage />} />
                <Route path="archived" element={<ArchivedAssistantsPage />} />
                <Route path=":assistantId/edit" element={<AssistantsEditPage />} />
                <Route path="create" element={<AssistantsCreatePage />} />
                <Route path="create-from-template" element={<CreateAssistantFromTemplatesPage />} />
              </Route>
              <Route path="users">
                <Route index element={<UsersPage />} />
                <Route path=":userId" element={<UserDetailPage />} />
              </Route>
              <Route path="groups">
                <Route index element={<GroupsPage />} />
              </Route>
              <Route path="tenant-settings">
                <Route index element={<TenantSettingsPage />} />
              </Route>
              <Route path="usage">
                <Route index element={<TenantUsageDashboardPage />} />
              </Route>
              <Route path="*" element={<NoPage />} />
            </Route>
            {/* group management */}
            <Route element={<GroupManagementLayout />}>
              <Route path="groups">
                <Route path=":groupId/assistants">
                  <Route index element={<GroupAssistantsPage />} />
                  <Route path="archived" element={<GroupArchivedAssistantsPage />} />
                  <Route path=":assistantId" element={<AssistantDetailPage />} />
                  <Route path=":assistantId/edit" element={<AssistantsEditPage />} />
                  <Route path="create" element={<AssistantsCreatePage />} />
                  <Route
                    path="create-from-template"
                    element={<CreateAssistantFromTemplatesPage />}
                  />
                </Route>
                <Route path=":groupId/users" element={<GroupUsersPage />} />
                <Route path=":groupId/users/add-users" element={<AddUsersToGroupPage />} />
              </Route>
            </Route>
          </Route>
          {/* administrator */}
          <Route
            path="/administrator"
            element={<RouterAdministratorGuard component={<AdministratorLayout />} />}
          >
            <Route index element={<Admin />} />
            <Route path="tenants">
              <Route index element={<TenantsPage />} />
              <Route path=":tenantId" element={<TenantDetailPage />} />
            </Route>
            <Route path="bots" element={<AdministratorBot />} />
            <Route path="assistant-templates">
              <Route index element={<AssistantTemplatesPage />} />
              <Route path=":assistantTemplateId">
                <Route index element={<AssistantTemplateDetailPage />} />
                <Route path="edit" element={<AssistantTemplateEditPage />} />
              </Route>
              <Route path="create" element={<AssistantTemplateCreatePage />} />
            </Route>
            <Route path="notifications">
              <Route index element={<NotificationsPage />} />
              <Route path="archived" element={<ArchivedNotificationsPage />} />
            </Route>
            <Route path="administrators">
              <Route index element={<AdministratorsPage />} />
            </Route>
            <Route path="*" element={<NoPage />} />
          </Route>
        </Route>
        {/* embedded ui */}
        <Route
          path="/embed"
          element={
            <EmbedContextProvider>
              <EmbedPage />
            </EmbedContextProvider>
          }
        />
      </Routes>
    </HashRouter>
  );
};

const App = () => {
  return <Pages />;
};

export default withLDProvider({
  clientSideID: import.meta.env.VITE_LAUNCH_DARKLY_CLIENT_SIDE_ID,
})(App);

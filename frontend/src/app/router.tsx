import { Suspense, lazy, type ReactNode } from "react";
import { createBrowserRouter, Outlet } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { EmptyState, Spinner } from "@/components/ui";

const LandingPage = lazy(() => import("@/features/landing/LandingPage"));
const LoginPage = lazy(() => import("@/features/auth/LoginPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/DashboardPage"));
const DiscoverPage = lazy(() => import("@/features/discovery/DiscoverPage"));
const CreateProjectPage = lazy(() => import("@/features/projects/CreateProjectPage"));
const ProjectDetailsPage = lazy(() => import("@/features/projects/ProjectDetailsPage"));
const KnowledgePage = lazy(() => import("@/features/knowledge/KnowledgePage"));
const CreateProblemPage = lazy(() => import("@/features/knowledge/CreateProblemPage"));
const ProblemDetailsPage = lazy(() => import("@/features/knowledge/ProblemDetailsPage"));
const FieldReportsPage = lazy(() => import("@/features/field-reports/FieldReportsPage"));
const FieldReportDetailsPage = lazy(() => import("@/features/field-reports/FieldReportDetailsPage"));
const CountriesPage = lazy(() => import("@/features/countries/CountriesPage"));
const CountryHubPage = lazy(() => import("@/features/countries/CountryHubPage"));
const LeaderboardPage = lazy(() => import("@/features/leaderboard/LeaderboardPage"));
const MissionsPage = lazy(() => import("@/features/missions/MissionsPage"));
const MissionDetailsPage = lazy(() => import("@/features/missions/MissionDetailsPage"));
const ApiDirectoryPage = lazy(() => import("@/features/api-directory/ApiDirectoryPage"));
const ApiDetailsPage = lazy(() => import("@/features/api-directory/ApiDetailsPage"));
const MessagesPage = lazy(() => import("@/features/messaging/MessagesPage"));
const ProfilePage = lazy(() => import("@/features/profile/ProfilePage"));
const SettingsPage = lazy(() => import("@/features/profile/SettingsPage"));
const AdminPage = lazy(() => import("@/features/admin/AdminPage"));

function withSuspense(node: ReactNode) {
  return (
    <Suspense fallback={<Spinner label="…" />}>
      {node}
    </Suspense>
  );
}

function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16">
      <EmptyState title="404" description="Cette page est introuvable. — This page could not be found." />
    </div>
  );
}

function RootBoundary() {
  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    element: <RootBoundary />,
    children: [
      {
        element: <PublicLayout />,
        children: [
          { path: "/", element: withSuspense(<LandingPage />) },
          { path: "/login", element: withSuspense(<LoginPage />) },
          { path: "/knowledge", element: withSuspense(<KnowledgePage />) },
          { path: "/knowledge/:id", element: withSuspense(<ProblemDetailsPage />) },
          { path: "/field-reports", element: withSuspense(<FieldReportsPage />) },
          { path: "/field-reports/:id", element: withSuspense(<FieldReportDetailsPage />) },
          { path: "/countries", element: withSuspense(<CountriesPage />) },
          { path: "/countries/:code", element: withSuspense(<CountryHubPage />) },
          { path: "/leaderboard", element: withSuspense(<LeaderboardPage />) },
          { path: "/missions", element: withSuspense(<MissionsPage />) },
          { path: "/missions/:id", element: withSuspense(<MissionDetailsPage />) },
          { path: "/api-directory", element: withSuspense(<ApiDirectoryPage />) },
          { path: "/api-directory/:id", element: withSuspense(<ApiDetailsPage />) },
          { path: "/profile/:username", element: withSuspense(<ProfilePage />) },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { path: "/dashboard", element: withSuspense(<DashboardPage />) },
              { path: "/discover", element: withSuspense(<DiscoverPage />) },
              { path: "/knowledge/new", element: withSuspense(<CreateProblemPage />) },
              { path: "/projects/new", element: withSuspense(<CreateProjectPage />) },
              { path: "/projects/:id", element: withSuspense(<ProjectDetailsPage />) },
              { path: "/messages", element: withSuspense(<MessagesPage />) },
              { path: "/settings", element: withSuspense(<SettingsPage />) },
            ],
          },
        ],
      },
      {
        element: <ProtectedRoute adminOnly />,
        children: [
          {
            element: <AppLayout />,
            children: [{ path: "/admin", element: withSuspense(<AdminPage />) }],
          },
        ],
      },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

import { createBrowserRouter } from "react-router";
import Root from "./Root";
import HomePage from "./pages/HomePage";
import WorkflowPage from "./pages/WorkflowPage";
import StandardizedWorkflowsPage from "./pages/StandardizedWorkflowsPage";
import ProjectsPage from "./pages/ProjectsPage";
import ProfilePage from "./pages/ProfilePage";
import CalculatorPage from "./pages/CalculatorPage";
import DocsPage from "./pages/DocsPage";
import TeamsPage from "./pages/TeamsPage";
import AIModelPage from "./pages/AIModelPage";
import WorkflowDraftsPage from "./pages/WorkflowDraftsPage";
import ResearchAssistantPage from "./pages/ResearchAssistantPage";
import NMRDataPage from "./pages/NMRDataPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: HomePage },
      { path: "workflow", Component: WorkflowPage },
      { path: "standardized-workflows", Component: StandardizedWorkflowsPage },
      { path: "projects", Component: ProjectsPage },
      { path: "docs", Component: DocsPage },
      { path: "profile", Component: ProfilePage },
      { path: "calculator", Component: CalculatorPage },
      { path: "teams", Component: TeamsPage },
      { path: "ai-model", Component: AIModelPage },
      { path: "workflow-drafts", Component: WorkflowDraftsPage },
      { path: "assistant", Component: ResearchAssistantPage },
      { path: "nmr-data", Component: NMRDataPage },
    ],
  },
]);

import { createBrowserRouter } from "react-router";
import Root from "./Root";
import HomePage from "./pages/HomePage";
import WorkflowPage from "./pages/WorkflowPage";
import ProjectsPage from "./pages/ProjectsPage";
import ProfilePage from "./pages/ProfilePage";
import CalculatorPage from "./pages/CalculatorPage";
import TeamsPage from "./pages/TeamsPage";
import AIModelPage from "./pages/AIModelPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: HomePage },
      { path: "workflow", Component: WorkflowPage },
      { path: "projects", Component: ProjectsPage },
      { path: "profile", Component: ProfilePage },
      { path: "calculator", Component: CalculatorPage },
      { path: "teams", Component: TeamsPage },
      { path: "ai-model", Component: AIModelPage },
    ],
  },
]);

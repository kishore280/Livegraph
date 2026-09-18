import { createBrowserRouter, redirect, RouterProvider } from "react-router-dom";
import { createSession } from "./api/sessions";
import { SessionPage } from "./pages/SessionPage";

const router = createBrowserRouter([
  {
    path: "/",
    loader: async () => {
      const session = await createSession();
      return redirect(`/s/${session.session_id}`);
    },
  },
  {
    path: "/s/:sessionId",
    element: <SessionPage />,
  },
]);

export function App() {
  return <RouterProvider router={router} />;
}

import { MessageSquarePlusIcon, PlusIcon } from "lucide-react";
import { useCallback } from "react";

import { openCommandPalette } from "../commandPaletteBus";
import { useNewProjectlessThreadHandler } from "../hooks/useHandleNewThread";
import { useEnvironments } from "../state/environments";
import { Button } from "./ui/button";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "./ui/empty";
import { SidebarInset } from "./ui/sidebar";

export function NoProjectsHero() {
  const { environments } = useEnvironments();
  const handleNewProjectlessThread = useNewProjectlessThreadHandler();
  const openAddProject = useCallback(() => openCommandPalette({ open: "add-project" }), []);
  const startChat = useCallback(() => {
    const environmentId = environments[0]?.environmentId;
    if (!environmentId) {
      return;
    }
    void handleNewProjectlessThread(environmentId);
  }, [environments, handleNewProjectlessThread]);

  return (
    <SidebarInset className="h-dvh min-h-0 overflow-hidden overscroll-y-none bg-background text-foreground">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden bg-background">
        <Empty className="flex-1">
          <div className="w-full max-w-lg px-8 py-12">
            <EmptyHeader className="max-w-none">
              <EmptyTitle className="text-foreground text-2xl sm:text-3xl">
                What should we work on?
              </EmptyTitle>
              <EmptyDescription className="mt-2 text-sm text-muted-foreground/78">
                Start a chat without a project, or add a project when you have a folder ready.
              </EmptyDescription>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {environments.length > 0 ? (
                  <Button size="sm" onClick={startChat}>
                    <MessageSquarePlusIcon className="size-4" />
                    Start chat
                  </Button>
                ) : null}
                <Button size="sm" variant={environments.length > 0 ? "outline" : "default"} onClick={openAddProject}>
                  <PlusIcon className="size-4" />
                  Add project
                </Button>
              </div>
            </EmptyHeader>
          </div>
        </Empty>
      </div>
    </SidebarInset>
  );
}

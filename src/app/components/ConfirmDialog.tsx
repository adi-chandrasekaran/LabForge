import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  destructive = true,
  busy = false,
  onOpenChange,
  onConfirm,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  busy?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent
        className="border-border bg-background"
        style={{ fontFamily: "'JetBrains Mono', monospace" }}
      >
        <AlertDialogHeader>
          <AlertDialogTitle className="text-sm font-mono text-foreground">{title}</AlertDialogTitle>
          <AlertDialogDescription className="text-[10px] font-mono leading-relaxed text-muted-foreground">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="border-border bg-transparent text-[10px] font-mono text-muted-foreground hover:bg-secondary hover:text-foreground">
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={busy}
            onClick={(event) => {
              event.preventDefault();
              onConfirm();
            }}
            className={`text-[10px] font-mono ${
              destructive
                ? "border border-red-400/30 bg-red-500/90 text-white hover:bg-red-500"
                : "border border-[#00c9a7] bg-[#00c9a7] text-[#080c12] hover:bg-[#00b899]"
            }`}
          >
            {busy ? "WORKING..." : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

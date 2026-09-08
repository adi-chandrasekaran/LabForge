# Projects

A project is the top-level scientific container. Experimental workflows attach to projects, so each project gets its own tab on the `Workflow` page.

## Current Behavior

The `Projects` page now loads from the backend instead of hardcoded frontend data.

You can:

1. Open the `Projects` page.
2. Review the seeded showcase project cards:
   - `ANC2 Protein Purification`
   - `RPC10 Purification Process And Troubleshooting`
   - `CCL20 Transformation And Culture`
3. Create a new project from the `New Project` modal.
4. Open `Workflow` and confirm the new project has a new blank workflow tab.
5. Delete a project after confirming the destructive action.

## Local Showcase Data

On clean local seed, the app starts from only the three showcase projects above. Old known demo records are removed during local startup cleanup. New projects you create are preserved until you delete them.

Deleting a project also removes its linked experimental workflows and related local records.

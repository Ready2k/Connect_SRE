# Amazon Connect Flow Designer Features

---

## 1. Mini-Map Navigation

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/flow-minimap.html

### Description

In the lower-left corner of the flow designer there is a miniaturized view of the entire flow. This mini-map provides a drag-to-move overview with visual highlights that enable you to quickly navigate to any point in a flow. It is especially useful for large, complex flows where scrolling and panning would be slow.

### How to Use

- The mini-map appears in the **lower-left corner** of the flow designer canvas.
- **Toggle visibility:** Use the toggle control (arrow icon) next to the mini-map to show or hide it.
- **Navigate:** Click or tap anywhere on the mini-map to instantly move the main canvas view to that location.
- **Drag:** Click and drag within the mini-map for continuous movement of the view across the flow.

### Visual Highlights

The mini-map uses color coding to help you orient within the flow:

| Element | Color |
|---|---|
| Current viewport | Green outline |
| Selected blocks | Blue |
| Notes/annotations | Yellow |
| Search results | Orange |
| Termination blocks | Black |

### Additional Functionality

- **Reset button:** Returns the view to the **Entry** block and trims unused whitespace/space from the canvas.
- The mini-map updates in real time as you add, move, or delete blocks.

### Tips

- Use the mini-map in combination with search results (highlighted in orange) to quickly jump between matching blocks in a large flow.
- The Reset button is useful when you have zoomed or panned far from the starting point and want to re-center.

---

## 2. Custom Block Names

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/set-custom-flow-block-name.html

### Description

You can customize the display name of any flow block to help distinguish blocks at a glance. This is particularly useful when a flow contains multiple instances of the same block type (e.g., multiple "Play prompt" blocks). Custom block names also appear in **CloudWatch logs** under the `Identifier` field, making it easier to diagnose issues from log data.

### How to Set a Custom Block Name

There are **two methods:**

**Method 1: Via the block context menu**
1. On the block in the flow designer, click the **...** (three-dot/ellipsis) menu.
2. Choose **Add block name**.
3. Type your custom name.

**Method 2: Via the Property page**
1. Click on the block to open its configuration.
2. On the **Property** page, locate the block name field.
3. Type your custom name.

### Restrictions on Block Names

The following characters are **not allowed** in the block name or `Identifier` field:

```
% : ( \ / ) = $ , ; [ ] { }
```

The following strings are **not allowed** in the block name:

- `__proto__`
- `constructor`
- `__defineGetter__`
- `__defineSetter__`
- `toString`
- `hasOwnProperty`
- `isPrototypeOf`
- `propertyIsEnumerable`
- `toLocaleString`
- `valueOf`

### Tips

- Use descriptive names that indicate the block's purpose (e.g., "Greeting - English", "After-hours message") rather than generic names.
- Custom names propagate to CloudWatch logs, so use names that will help with debugging and log analysis.

---

## 3. Undo and Redo History

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/undo-redo-history.html

### Description

The flow designer supports undo and redo for actions performed on the canvas. You can step backward and forward through your editing history using toolbar buttons or keyboard shortcuts.

### How to Use

**Toolbar:**
- Click the **Undo** button on the toolbar to reverse the last action.
- Click the **Redo** button on the toolbar to re-apply a reversed action.
- Click the **Undo dropdown** button to view a full history of actions that can be undone.

**Keyboard Shortcuts:**
- **Undo:** `Ctrl+Z` (Windows) / `Ctrl+Z` (Mac)
- **Redo:** `Ctrl+Y` (Windows)

### Important Note for Mac Users

On a Mac, `Ctrl+Y` opens the browser history page instead of performing a redo. Use the toolbar redo button instead.

### Undo History Dropdown

Clicking the dropdown arrow next to the Undo button on the toolbar reveals a list of recent actions. You can select any action in the list to undo back to that point.

### Limits

| Item | Limit |
|---|---|
| History limit | Up to **100 actions** can be undone |
| Dragging unconnected connector | This action **cannot** be undone |
| Folding of notes | This action **cannot** be undone |
| Page reload | Undo history is **not retained** after a page reload |

### Tips

- The undo history is session-based only. If you reload the page, all undo/redo history is lost.
- Before making major structural changes, consider saving the flow first so you can revert via version control if undo is insufficient.
- Be aware that certain actions (dragging unconnected connectors, folding notes) are not tracked in the undo history.

---

## 4. Add Notes/Annotations to Blocks

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/add-notes-to-block.html

### Description

You can add annotation notes to blocks in the flow designer. Notes appear as yellow boxes on the canvas and allow you to leave comments that other team members can view. This is useful for documenting the purpose of specific blocks, leaving instructions, or flagging items for review.

### How to Add a Note

**Toolbar:**
1. On the toolbar, click the **Annotation** button.
2. A yellow note box appears on the canvas.
3. Type your content (up to 1,000 characters).

**Keyboard Shortcut:**
- `Ctrl + Alt + N` (with cursor on the flow designer canvas)

### Working with Notes

- **Move notes:** Drag a note around the canvas to reposition it.
- **Attach to a block:** Drag a note near a block to attach it. The note will stay associated with that block.
- **View all notes:** Use the dropdown menu to see a list of all notes in the flow. Click any note in the list to navigate directly to it.
- **Search notes:** Use the search box in the notes dropdown to search across all notes in the flow.

### Supported Content

- Unicode characters are supported.
- Emojis are supported.
- You can copy and paste text into the note box.
- You can undo and redo within the note box.

### Behavior with Block Deletion

- When a block is **deleted**, all notes attached to that block are also deleted.
- When a block is **restored** (via undo), the notes attached to it are also restored.

### Limits

| Item | Limit |
|---|---|
| Character limit | **1,000 characters** per note |
| Attachment limit | **5 notes** per block |
| Note limit | **100 notes** per flow |

### Tips

- Notes appear as yellow highlights on the mini-map, making them easy to locate visually.
- Use notes to document decision logic, business rules, or configuration rationale so other flow editors understand the "why" behind block configurations.
- Notes are saved with the flow, so they persist across sessions and are visible to all users with access to the flow.

---

## 5. Copy and Paste Flows

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/copy-paste-contact-flows.html

### Description

You can select, cut, copy, and paste complete flows or multiple blocks within or across flows. This feature uses the system clipboard and preserves:

- All configured settings in the selected flow blocks.
- The layout arrangements (positions of blocks on the canvas).
- The connections between blocks.

### How to Copy and Paste

**Using the Toolbar:**
- Select blocks, then use the **Copy** button on the flow designer toolbar.

**Using Keyboard Shortcuts:**

**Windows:**
1. To select multiple blocks: Hold `Ctrl` and click the blocks you want.
2. Copy: `Ctrl+C`
3. Paste: `Ctrl+V`
4. Cut: `Ctrl+X`

**Mac:**
1. To select multiple blocks: Hold `Cmd` and click the blocks you want.
2. Copy: `Cmd+C`
3. Paste: `Cmd+V`
4. Cut: `Cmd+X`

### Steps (Windows Example)

1. Press and hold the `Ctrl` key, then click each block you want to select.
2. With your cursor on the flow designer canvas, press `Ctrl+C` to copy the blocks.
3. Press `Ctrl+V` to paste the blocks onto the canvas.

### Cross-Flow Copy

- You can copy blocks from one flow and paste them into a different flow.
- Open the source flow, select and copy the blocks, then navigate to the destination flow and paste.

### Limitations and Tips

- Amazon Connect uses the **system clipboard** for this feature.
- Paste will **not work** if you manually edit the JSON in your clipboard and introduce a typo or other error.
- Paste will **not work** if you have multiple items saved to your clipboard (e.g., from a clipboard manager).
- All block settings, layout positions, and connections are preserved in the copy.

---

## 6. Archive, Delete, and Restore Flows

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/delete-contact-flow.html

### Description

Flows and modules must be **archived** before they can be deleted from your Amazon Connect instance. Archived flows and modules can be **restored**. However, once a flow or module is **deleted**, it is permanently removed and cannot be recovered.

### Important Things to Know

- **No validation on archive:** Amazon Connect does **not** validate whether the flow or module you are archiving is currently being used in other published flows. It does **not** warn you that the flow is in use. Use caution.
- **Default flows cannot be archived or deleted.** Attempting to archive a default flow produces an error message.
- **Associated resources block archiving:** Flows and modules that are associated with queues, quick connects, or phone numbers **cannot** be archived. You must disassociate the resources from the flows before archiving.
- **Quota impact:** Archived flows and modules **still count** toward your "Flows per instance" and "Modules per instance" service quotas. You must delete them to free up quota.

### Required Permissions

| Action | Required Permission |
|---|---|
| Archive a flow | **Numbers and flows > Flows > Edit** |
| Archive a module | **Numbers and flows > Flow modules > Edit** |
| Restore a flow | **Numbers and flows > Flows > Edit** |
| Restore a module | **Numbers and flows > Flow modules > Edit** |
| Delete a flow | **Numbers and flows > Flows > Remove** |
| Delete a module | **Numbers and flows > Flow modules > Remove** |

### Archive a Flow or Module

**Option 1: From the flow designer**

1. Log in with a user account that has the required Edit permission.
2. Navigate to **Routing > Flows**.
3. Open the flow or module you want to archive.
4. On the flow designer page, click the dropdown menu and choose **Archive**.
5. Confirm you want to archive.
6. To locate the archived item, choose **View archive**.

**Option 2: From the Flows list page**

1. On the **Flows** page, search for the flow or module.
2. Click the **...** (ellipsis) menu next to the flow.
3. Choose **Archive**.

### Restore an Archived Flow or Module

**Option 1: From the archive list**

1. Log in with a user account that has the required Edit permission.
2. Navigate to **Routing > Flows**.
3. Click **View archive** on the Flows page.
   - For modules: go to the **Modules** tab first, then click **View archive**.
4. On the **Flows Archive** page, find the flow or module, click **...** under Actions, and choose **Restore**.

**Option 2: From the flow designer**

1. Open the archived flow or module in the flow designer.
2. From the dropdown menu, choose **Restore**.

### Delete an Archived Flow or Module

Deletion can be done manually via the admin website or programmatically via the `DeleteContactFlow` API.

**WARNING:** Deleted flows and modules **cannot be restored**. They are permanently deleted.

**Option 1: From the archive list**

1. Log in with a user account that has the required Remove permission.
2. Navigate to **Routing > Flows**.
3. Click **View archive**.
   - For modules: go to the **Modules** tab first, then click **View archive**.
4. On the **Flows Archive** page, find the flow or module, click **...** under Actions, and choose **Delete**.
5. Confirm the deletion.

**Option 2: From the flow designer**

1. Open the archived flow or module in the flow designer.
2. From the dropdown menu, choose **Delete**.
3. Confirm the deletion.

### Programmatic Deletion

Use the [DeleteContactFlow API](https://docs.aws.amazon.com/connect/latest/APIReference/API_DeleteContactFlow.html) to delete archived flows programmatically.

### Tips

- Always verify that a flow is not referenced by other flows, queues, quick connects, or phone numbers before archiving.
- Since archived flows still count toward quotas, periodically review and delete flows you no longer need.
- Consider using version control (roll back) instead of archiving if you just want to revert changes rather than remove a flow.

---

## 7. Flow Version Control / Roll Back a Flow

**Source:** https://docs.aws.amazon.com/connect/latest/adminguide/flow-version-control.html

### Description

Amazon Connect maintains a version history of published flows. You can view previous versions of a flow, compare how a flow has changed over time, and roll back to any previously published version by re-publishing it. This is useful for investigating changes, reverting problematic updates, or restoring a known-good configuration.

### View a Previous Version of a Flow

1. In the flow designer, open the flow you want to inspect.
2. Click the **Latest: Published** dropdown at the top of the designer.
3. A list of previously published versions appears, each with a timestamp.
   - For default flows provided with your Amazon Connect instance, the oldest entry in the list is the original version. Its date matches when your instance was created.
4. Choose the version you want to view. The flow opens with all blocks and their configurations visible for that version.

### After Viewing a Previous Version

Once you have a previous version open, you can:

- **Return to the latest version:** Select the most recent entry from the **Latest: Published** dropdown.
- **Save as a new flow:** Choose **Save as** from the dropdown to save the previous version with a new name.
- **Overwrite with same name:** Choose **Save** from the dropdown to save over the current flow with the same name.
- **Publish immediately:** Choose **Publish** to push the previous version directly into production.

### Roll Back a Flow

1. In the flow designer, open the flow you want to roll back.
2. Use the dropdown to select the version you want to roll back to.
   - If you choose **Latest**, it reverts to the most recent published version. If there is no published version, it reverts to the most recent saved version.
3. Choose **Publish** to push that version into production.

### Tag-Based Access Control Restriction

For users with **tag-based access controls** configured on their security profile, the version dropdown is restricted to only:
- **Latest: Published**
- **Latest: Saved**

They cannot browse the full version history. To learn more, see [Apply tag-based access control in Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/tag-based-access-control.html).

### View Historical Changes Across All Flows

At the bottom of the **Flows** page, there is a **View historical changes** link. This provides a consolidated view of all changes across all flows. You can filter by:
- Specific flow
- Date range
- User name (who made the change)

### Tips

- Use version history to audit who changed what and when, especially for production flows.
- Before publishing major changes, note the current version timestamp so you can easily roll back if needed.
- The "Save as" option is useful for creating a backup copy of a flow before making experimental changes.
- Rolling back is as simple as selecting the old version and clicking Publish -- no need to manually reconfigure blocks.
- Tag-based access controls limit version visibility, so admin/unrestricted users should handle version rollbacks when TBAC is in use.

import { PutApiMethods } from "@/types/api.types";

export async function toggleStatus(
  contentId: string,
  currentStatus: string,
  contentType: "monitored" | "watched",
  api: PutApiMethods
) {
  try {
    const newStatus = currentStatus === "Active" ? "Not Active" : "Active";

    if (contentType === "monitored") {
      await api.updateProtectedContentStatusById(contentId, newStatus);
    } else {
      await api.updateWatchedContentStatusById(contentId, newStatus);
    }

    return newStatus;
  } catch (error) {
    console.error("Error updating content status:", error);
    throw new Error("Failed to update content status.");
  }
}

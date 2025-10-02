import { BaseContent } from "@/types/content.types";
import { InstagramContent } from "@/types/database.types";

export const formatNumber = (num: number): string => {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return String(num);
};

export const mapApiResponseToContent = (
  response: InstagramContent[]
): BaseContent[] => {
  return response.map((item) => {
    const baseContent: BaseContent = {
      id: item.id,
      code: item.media_id,
      status: item.status,
      caption: item.caption || "",
      username: item.username,
      imageUrl: item.imageUrl,
      publishDate: item.publishDate,
      createdAt: item.createdAt,
      igPlayCount: item.igPlayCount || 0,
      commentCount: item.commentCount,
      reshareCount: item.reshareCount || 0,
      likeCount: item.likeCount,
      nbAlerts: 0,
      updatedAt: item.updatedAt,
      isWatched: item.isWatched,
      isMonitored: item.isMonitored,
      monitoredBy: item.monitoredBy ? [item.monitoredBy] : [],
    };
    return baseContent;
  });
};

export const filterContent = (
  data: BaseContent[],
  searchTerm: string
): BaseContent[] => {
  if (!searchTerm.trim()) return data;

  return data.filter(
    (item) =>
      item.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.caption.toLowerCase().includes(searchTerm.toLowerCase())
  );
};

export const paginateData = (
  data: BaseContent[],
  currentPage: number,
  rowsPerPage: number
): BaseContent[] => {
  return data.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
};

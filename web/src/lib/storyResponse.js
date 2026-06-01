export function getStoryPayload(response) {
  const data = response?.data;
  if (!data || data.type !== "story") return null;

  const story = data.story || {
    title: data.title,
    content: data.content,
    level: data.level,
    theme: data.theme,
    audio_file_url: data.audio_file_url,
  };

  if (!story?.content) return null;

  return {
    story: {
      ...story,
      id: story.id,
    },
    audioUrl: data.audio_url || story.audio_file_url || "",
  };
}

export function saveCurrentStory(response) {
  const payload = getStoryPayload(response);
  if (!payload) return null;

  sessionStorage.setItem("currentStory", JSON.stringify(payload));
  return payload;
}

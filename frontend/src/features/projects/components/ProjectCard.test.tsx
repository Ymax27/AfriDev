import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import "@/i18n";
import { ProjectCard } from "@/features/projects/components/ProjectCard";
import type { Project } from "@/types/api";

const project: Project = {
  id: "p1",
  name: "SawaPay",
  slug: "sawapay",
  description: "Paiement mobile money unifié pour les PME.",
  technologies: ["React", "FastAPI"],
  tags: [],
  category: "fintech",
  collaboration_mode: "open_to_contributors",
  ownership_status: "pending",
  is_published: true,
  is_demo: true,
  is_featured: false,
  view_count: 12,
  github_stars: 3,
  creator: {
    id: "u1",
    username: "amina",
    full_name: "Amina",
    level: "contributor",
    reputation_points: 40,
  },
  created_at: "2026-01-01T00:00:00Z",
  likes_count: 5,
  contributions_count: 2,
  feedback_count: 1,
  liked_by_me: false,
  passed_by_me: false,
};

describe("ProjectCard", () => {
  it("renders the project name, author and demo flag", () => {
    render(
      <MemoryRouter>
        <ProjectCard project={project} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "SawaPay" })).toBeInTheDocument();
    expect(screen.getByText(/@amina/)).toBeInTheDocument();
    expect(screen.getByText("DEMO")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
  });
});

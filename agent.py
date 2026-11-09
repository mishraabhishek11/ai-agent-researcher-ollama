from ollama import chat

from tools import (
    search_web,
    read_webpage,
    add_research_note,
    get_research_notes,
    verify_finding,
    get_verified_research_notes
)


MODEL = "qwen3:4b"


AVAILABLE_TOOLS = {
    "search_web": search_web,
    "read_webpage": read_webpage,
    "add_research_note": add_research_note,
    "get_research_notes": get_research_notes,
    "verify_finding": verify_finding
}


TOOLS = [
    search_web,
    read_webpage,
    add_research_note,
    get_research_notes,
    verify_finding
]


def generate_report(
    user_request,
    verified_notes
):
    """
    Generate a research report from
    verified research findings.
    """

    research_text = "\n\n".join(
        [
            (
                f"Source: {note['source']}\n"
                f"Finding: {note['finding']}\n"
                f"Evidence: {note['evidence']}"
            )
            for note in verified_notes
        ]
    )

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional research "
                    "report writer. "
                    "Write a clear, structured report "
                    "using only the supplied verified "
                    "research findings. "
                    "Do not invent facts or sources. "
                    "If the available research is "
                    "insufficient for a section, say so."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Research request:\n"
                    f"{user_request}\n\n"
                    f"Verified research findings:\n"
                    f"{research_text}\n\n"
                    "Create a report with the following "
                    "sections:\n"
                    "1. Executive Summary\n"
                    "2. Introduction\n"
                    "3. Key Findings\n"
                    "4. Analysis\n"
                    "5. Limitations\n"
                    "6. Conclusion\n"
                    "7. Sources\n\n"
                    "List the sources used in the "
                    "verified findings. "
                    "Do not create URLs that were not "
                    "provided in the research findings."
                )
            }
        ]
    )

    return response.message.content


def research_agent(
    user_request,
    max_steps=100
):
    """
    Run the autonomous research agent.

    The agent must collect and verify research
    findings before it is allowed to finish.
    """

    plan = create_research_plan(
        user_request
    )

    print("\n" + "=" * 60)
    print("RESEARCH PLAN")
    print("=" * 60)
    print(plan)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research agent. "

                "Investigate the user's request using "
                "the available tools. "

                "Follow the research plan carefully. "

                "First search for relevant sources. "

                "After reading a useful source, "
                "extract important findings and call "
                "add_research_note to store them. "

                "After storing an important finding, "
                "use verify_finding to determine whether "
                "the evidence actually supports the finding. "

                "Continue researching until the research "
                "question has been adequately investigated. "

                "Do not finish the research with zero "
                "verified findings. "

                "Do not invent sources or evidence."
            )
        },
        {
            "role": "user",
            "content": (
                f"Research request:\n{user_request}\n\n"
                f"Research plan:\n{plan}"
            )
        }
    ]

    for step in range(max_steps):

        print(
            f"\n--- Agent Step {step + 1} ---"
        )

        response = chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS
        )

        messages.append(
            response.message
        )

        # -------------------------------------------------
        # The LLM did not request a tool.
        # Do NOT immediately accept this as completion.
        # First check whether verified findings exist.
        # -------------------------------------------------

        if not response.message.tool_calls:

            verified_notes = (
                get_verified_research_notes()
            )

            if verified_notes:

                print(
                    "\nResearch complete."
                )

                print(
                    "Verified findings collected:",
                    len(verified_notes)
                )

                return response.message.content

            else:

                print(
                    "\nAgent attempted to finish "
                    "without verified findings."
                )

                print(
                    "Continuing research..."
                )

                messages.append({
    "role": "user",
    "content": (
        "You attempted to finish without collecting "
        "any verified research findings. "
        "You MUST perform another research action now. "
        "Do not provide a final answer. "
        "Choose one of these actions:\n"
        "1. Call search_web to find another source.\n"
        "2. Call read_webpage to inspect a source.\n"
        "3. Call add_research_note after extracting "
        "a finding from a source.\n"
        "4. Call verify_finding after storing a finding.\n"
        "You must call a tool in your next response."
    )
})

                continue

        # -------------------------------------------------
        # Execute every tool requested by the model.
        # -------------------------------------------------

        for tool_call in (
            response.message.tool_calls
        ):

            tool_name = (
                tool_call.function.name
            )

            arguments = (
                tool_call.function.arguments
            )

            print(
                f"\nCalling tool: {tool_name}"
            )

            print(
                f"Arguments: {arguments}"
            )

            tool_function = (
                AVAILABLE_TOOLS.get(
                    tool_name
                )
            )

            if tool_function is None:

                result = (
                    f"Unknown tool: "
                    f"{tool_name}"
                )

            else:

                try:

                    result = tool_function(
                        **arguments
                    )

                except Exception as e:

                    result = {
                        "status": "error",
                        "tool": tool_name,
                        "error": str(e)
                    }

                    print(
                        f"Tool error: {e}"
                    )

            messages.append({
                "role": "tool",
                "content": str(result),
                "tool_name": tool_name
            })

    return (
        "The agent reached its maximum "
        "number of steps before completing "
        "the research."
    )


def create_research_plan(
    user_request
):
    """
    Create a concise research plan.
    """

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research planning assistant. "

                    "Create a concise and ordered research "
                    "plan for the user's research request. "

                    "The plan should identify the main "
                    "research objectives that need to be "
                    "investigated. "

                    "Return only the numbered research steps."
                )
            },
            {
                "role": "user",
                "content": user_request
            }
        ]
    )

    return response.message.content
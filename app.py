import streamlit as st

from core.auth import get_mock_users
from core import roles
from core import repository
from core.styles import apply_theme, page_header

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Change Tracker POC", layout="wide")

# Initialize DB tables (safe to call every run)
repository.init_db()

def get_display_name_for_user_id(user_id: str) -> str:
    """
    For the POC, map stored user IDs to human-friendly names.
    """
    for u in get_mock_users():
        if u.id == user_id:
            return u.display_name
    if user_id == "admin-seed":
        return "Seeded Admin Record Owner"
    return user_id


def get_current_user():
    """
    Decide who is 'logged in' right now via a sidebar dropdown.
    """
    users = get_mock_users()

    if "current_user_index" not in st.session_state:
        st.session_state["current_user_index"] = 0  # default: first user

    selected_index = st.sidebar.selectbox(
        "Current user",
        options=list(range(len(users))),
        format_func=lambda i: users[i].display_name,
        index=st.session_state["current_user_index"],
    )

    st.session_state["current_user_index"] = selected_index
    return users[selected_index]


def show_my_records(user):
    """
    Render the 'My Records' page with actual data from the database.
    """
    st.title("📂 My Records")

    records = repository.list_records_for_user(user)

    if not records:
        st.info(
            "No records found yet for your role. "
            "Once we add creation flows, you'll see them here."
        )
        return

    table_rows = []
    for r in records:
        table_rows.append(
            {
                "Title": r.title,
                "Type": r.record_type,
                "Status": r.status,
                "Created At (Toronto)": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "Created By": r.created_by,
            }
        )

    st.write(
        f"Showing **{len(table_rows)}** record(s) visible to "
        f"**{user.display_name}** (`{user.role}`)."
    )
    st.table(table_rows)


def diff_ai_metadata(old_meta: dict, new_meta: dict):
    """
    Compare old vs new ai_metadata and return a list of
    (field_path, old_value, new_value) where they differ.
    """
    overrides = []

    old_meta = old_meta or {}
    new_meta = new_meta or {}

    # Framework tags
    old_framework = old_meta.get("framework_tags", []) or []
    new_framework = new_meta.get("framework_tags", []) or []
    if old_framework != new_framework:
        overrides.append(
            ("ai_metadata.framework_tags", old_framework, new_framework)
        )

    # Capability groups
    old_caps = old_meta.get("capability_groups", []) or []
    new_caps = new_meta.get("capability_groups", []) or []
    if old_caps != new_caps:
        overrides.append(
            ("ai_metadata.capability_groups", old_caps, new_caps)
        )

    return overrides


def show_editor(user):
    """
    Render the 'Record Editor' page.

    This page now uses tabs:
    - "Create New" for new records
    - "Edit + Comments" for working on existing records
    """

    page_header("✏️", "Record Workspace", "Create new use cases or refine existing ones.")

    if roles.is_viewer(user):
        st.info(
            "You are logged in as a read-only Viewer. "
            "Viewers cannot create or edit records."
        )
        return

    tab_create, tab_edit = st.tabs(["➕ Create New", "🛠 Edit + Comments"])

    # ----- TAB 1: CREATE NEW -----
    with tab_create:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"Create a new AI Use Case as **{user.display_name}** (`{user.role}`)."
        )
        st.caption("Start as a draft or directly mark as submitted for review.")
        with st.form("new_record_form"):
            title = st.text_input("Use Case Title", placeholder="e.g., Fraud Detection in Benefits")
            business_problem = st.text_area(
                "Business Problem",
                placeholder="What problem are you trying to solve?",
                height=100,
            )
            description = st.text_area(
                "Description",
                placeholder="Describe the AI solution at a high level.",
                height=150,
            )

            st.markdown("**AI Metadata (simple for now)**")
            framework_tags_str = st.text_input(
                "Framework Tags (comma-separated)",
                placeholder="e.g., Risk & Governance, Data & Analytics",
            )
            capability_groups_str = st.text_input(
                "Capability Groups (comma-separated)",
                placeholder="e.g., Fraud Detection, NLP",
            )

            status = st.selectbox(
                "Initial Status",
                options=["draft", "submitted"],
                index=0,
                help="In the real tool, you'd likely start as draft, then submit later.",
            )

            submitted_new = st.form_submit_button("💾 Create Record")

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted_new:
            if not title.strip():
                st.error("Title is required to create a record.")
            else:
                framework_tags = [
                    t.strip() for t in framework_tags_str.split(",") if t.strip()
                ]
                capability_groups = [
                    t.strip() for t in capability_groups_str.split(",") if t.strip()
                ]

                content = {
                    "business_problem": business_problem.strip(),
                    "description": description.strip(),
                    "ai_metadata": {
                        "framework_tags": framework_tags,
                        "capability_groups": capability_groups,
                    },
                }

                record = repository.create_record_with_initial_version(
                    title=title.strip(),
                    record_type="ai_use_case",
                    content=content,
                    user=user,
                    status=status,
                )

                st.success(
                    f"Record **'{record.title}'** created successfully as **{record.status}**!"
                )
                st.info(
                    "You can switch to **My Records** in the sidebar to see it in your list."
                )

    # ----- TAB 2: EDIT + COMMENTS -----
    with tab_edit:
        records = repository.list_records_for_user(user)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Select a record to edit")

        if not records:
            st.info(
                "No records available to edit based on your role. "
                "Try creating a new record first."
            )
            st.markdown('</div>', unsafe_allow_html=True)
            return

        options = {}
        for r in records:
            label = f"{r.title} [{r.status}] (Created by: {get_display_name_for_user_id(r.created_by)})"
            options[label] = r.id

        selected_label = st.selectbox("Record", list(options.keys()))
        selected_record_id = options[selected_label]
        st.markdown('</div>', unsafe_allow_html=True)

        # Fetch record + current version
        record = repository.get_record_by_id(selected_record_id)
        if not record:
            st.error("Selected record not found.")
            return

        current_version = repository.get_current_version(record.id)
        if not current_version:
            st.error("No current version found for this record.")
            return

        existing_content = current_version.content or {}
        existing_bp = existing_content.get("business_problem", "")
        existing_desc = existing_content.get("description", "")
        existing_meta = existing_content.get("ai_metadata", {}) or {}
        existing_framework_tags = existing_meta.get("framework_tags", [])
        existing_capability_groups = existing_meta.get("capability_groups", [])

        framework_tags_default = ", ".join(existing_framework_tags)
        capability_groups_default = ", ".join(existing_capability_groups)

        # EDIT FORM CARD
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Edit current version")

        st.caption(
            f"Current version: **v{current_version.version_number}** "
            f"· Last updated {current_version.created_at.strftime('%Y-%m-%d %H:%M')} "
            f"by **{current_version.created_by_name}**"
        )

        with st.form("edit_record_form"):
            title = st.text_input("Use Case Title", value=record.title)
            business_problem = st.text_area(
                "Business Problem",
                value=existing_bp,
                height=100,
            )
            description = st.text_area(
                "Description",
                value=existing_desc,
                height=150,
            )

            st.markdown("**AI Metadata (simple for now)**")
            framework_tags_str = st.text_input(
                "Framework Tags (comma-separated)",
                value=framework_tags_default,
            )
            capability_groups_str = st.text_input(
                "Capability Groups (comma-separated)",
                value=capability_groups_default,
            )

            status = st.selectbox(
                "New Status",
                options=["draft", "submitted"],
                index=["draft", "submitted"].index(record.status)
                if record.status in ["draft", "submitted"]
                else 0,
                help="Change the status if needed (e.g., move from draft to submitted).",
            )

            submitted_edit = st.form_submit_button("💾 Save New Version")

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted_edit:
            if not title.strip():
                st.error("Title is required.")
                return

            framework_tags = [
                t.strip() for t in framework_tags_str.split(",") if t.strip()
            ]
            capability_groups = [
                t.strip() for t in capability_groups_str.split(",") if t.strip()
            ]

            updated_content = {
                "business_problem": business_problem.strip(),
                "description": description.strip(),
                "ai_metadata": {
                    "framework_tags": framework_tags,
                    "capability_groups": capability_groups,
                },
            }

            # Determine if this is an override (admin changing metadata)
            old_meta = existing_meta
            new_meta = updated_content["ai_metadata"]
            overrides = diff_ai_metadata(old_meta, new_meta)

            if roles.is_admin(user) and overrides:
                version_type = "override"
            else:
                version_type = "edit"

            new_version = repository.create_new_version(
                record_id=record.id,
                new_title=title.strip(),
                content=updated_content,
                user=user,
                version_type=version_type,
                new_status=status,
            )

            if version_type == "override":
                repository.log_override_events(
                    record_id=record.id,
                    version_id=new_version.id,
                    overrides=overrides,
                    user=user,
                )
                st.success(
                    f"Override version **{new_version.version_number}** saved for "
                    f"record **'{title.strip()}'** with status **{status}**."
                )
                st.info("Metadata overrides have been logged in the audit trail.")
            else:
                st.success(
                    f"New version **{new_version.version_number}** saved for "
                    f"record **'{title.strip()}'** with status **{status}**."
                )
                st.info("You can view the version history on the **History** page.")

        # COMMENTS CARD
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💬 Comments on this Use Case")

        comments = repository.list_comments_for_record(record.id)

        if not comments:
            st.info("No comments yet on this record. Start the conversation below.")
        else:
            for c in comments:
                role_label = c.role.upper()
                can_manage = roles.is_admin(user) or (c.author_id == user.id)

                with st.container():
                    st.markdown(
                        f"**{c.author_name}** ({role_label}) "
                        f"· {c.created_at.strftime('%Y-%m-%d %H:%M')} (Toronto)"
                    )
                    st.write(c.text)

                    if can_manage:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit", key=f"edit_comment_{c.id}"):
                                st.session_state["editing_comment_id"] = c.id
                                st.session_state["editing_comment_text"] = c.text
                        with col2:
                            if st.button("Delete", key=f"delete_comment_{c.id}"):
                                repository.delete_comment(c.id)
                                st.success("Comment deleted.")
                                st.rerun()

                    st.markdown("---")

        if roles.is_viewer(user):
            st.info("Viewers cannot add or modify comments.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        editing_comment_id = st.session_state.get("editing_comment_id")

        if editing_comment_id:
            st.markdown("**✏️ Edit comment**")
            edit_default = st.session_state.get("editing_comment_text", "")
            edit_text = st.text_area(
                "Update your comment",
                value=edit_default,
                height=100,
                key="edit_comment_text_area",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Save changes"):
                    if not edit_text.strip():
                        st.error("Comment cannot be empty.")
                    else:
                        repository.update_comment(editing_comment_id, edit_text.strip())
                        st.success("Comment updated.")
                        st.session_state["editing_comment_id"] = None
                        st.rerun()
            with col2:
                if st.button("❌ Cancel edit"):
                    st.session_state["editing_comment_id"] = None
                    st.rerun()
        else:
            st.markdown("**Add a new comment**")
            with st.form("add_comment_form"):
                comment_text = st.text_area(
                    "Comment",
                    placeholder="Leave feedback, request changes, or respond...",
                    height=100,
                )
                comment_submitted = st.form_submit_button("💭 Post Comment")

            if comment_submitted:
                if not comment_text.strip():
                    st.error("Comment cannot be empty.")
                else:
                    repository.add_comment(
                        record_id=record.id,
                        version_id=current_version.id,
                        text=comment_text.strip(),
                        user=user,
                    )
                    st.success("Comment added successfully!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)



def show_history(user):
    """
    Render the 'Version History' page.

    Uses tabs:
    - Timeline
    - Inspect
    - Compare Versions
    - Override History
    """
    page_header("🕒", "Version History", "Inspect and compare every change made to a use case.")

    records = repository.list_records_for_user(user)

    if not records:
        st.info(
            "No records available to view history for based on your role. "
            "Try creating a record first."
        )
        return

    # Record selection card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Select a record")

    options = {}
    for r in records:
        label = f"{r.title} [{r.status}] (Created by: {get_display_name_for_user_id(r.created_by)})"
        options[label] = r.id

    selected_label = st.selectbox("Record", list(options.keys()))
    selected_record_id = options[selected_label]
    st.markdown('</div>', unsafe_allow_html=True)

    versions = repository.list_versions_for_record(selected_record_id)
    if not versions:
        st.warning("No versions found for this record (this shouldn't normally happen).")
        return

    version_label_map = {}
    for v in versions:
        lbl = f"v{v.version_number} - {v.version_type} - {v.created_at.strftime('%Y-%m-%d %H:%M')} by {v.created_by_name}"
        version_label_map[lbl] = v

    tab_timeline, tab_inspect, tab_compare, tab_overrides = st.tabs(
        ["📜 Timeline", "🔎 Inspect", "🆚 Compare Versions", "🧾 Override History"]
    )

    # ---- TIMELINE ----
    with tab_timeline:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Version Timeline")

        rows = []
        for v in versions:
            rows.append(
                {
                    "Version #": v.version_number,
                    "Type": v.version_type,
                    "Created By": v.created_by_name,
                    "Created At (Toronto)": v.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        st.table(rows)
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- INSPECT ----
    with tab_inspect:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Inspect a Specific Version")

        inspect_label = st.selectbox(
            "Choose a version",
            list(version_label_map.keys()),
            index=len(version_label_map) - 1,  # latest
        )
        inspect_version = version_label_map[inspect_label]
        inspect_content = inspect_version.content or {}
        inspect_meta = inspect_content.get("ai_metadata", {}) or {}

        st.markdown(
            f"**Selected Version:** v{inspect_version.version_number} ({inspect_version.version_type})"
        )
        st.caption(
            f"Created by **{inspect_version.created_by_name}** on "
            f"{inspect_version.created_at.strftime('%Y-%m-%d %H:%M')} (Toronto)"
        )

        st.markdown("**Business Problem**")
        st.write(inspect_content.get("business_problem", ""))

        st.markdown("**Description**")
        st.write(inspect_content.get("description", ""))

        st.markdown("**AI Metadata**")
        st.json(inspect_meta)

        st.markdown('</div>', unsafe_allow_html=True)

    # ---- COMPARE ----
    with tab_compare:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Compare Two Versions")

        version_labels_sorted = list(version_label_map.keys())

        col1, col2 = st.columns(2)
        with col1:
            base_label = st.selectbox(
                "Base version",
                version_labels_sorted,
                index=0,
                key="base_version_select",
            )
        with col2:
            compare_label = st.selectbox(
                "Compare to version",
                version_labels_sorted,
                index=len(version_labels_sorted) - 1,
                key="compare_version_select",
            )

        base_version = version_label_map[base_label]
        compare_version = version_label_map[compare_label]

        if st.button("🔍 Show Differences"):
            if base_version.id == compare_version.id:
                st.warning("Please select two different versions to compare.")
            else:
                base_content = base_version.content or {}
                base_meta = base_content.get("ai_metadata", {}) or {}

                compare_content = compare_version.content or {}
                compare_meta = compare_content.get("ai_metadata", {}) or {}

                diff_rows = []

                if base_content.get("business_problem", "") != compare_content.get("business_problem", ""):
                    diff_rows.append(
                        {
                            "Field": "business_problem",
                            "Base": base_content.get("business_problem", ""),
                            "Compare": compare_content.get("business_problem", ""),
                        }
                    )

                if base_content.get("description", "") != compare_content.get("description", ""):
                    diff_rows.append(
                        {
                            "Field": "description",
                            "Base": base_content.get("description", ""),
                            "Compare": compare_content.get("description", ""),
                        }
                    )

                base_framework = base_meta.get("framework_tags", []) or []
                compare_framework = compare_meta.get("framework_tags", []) or []
                if base_framework != compare_framework:
                    diff_rows.append(
                        {
                            "Field": "ai_metadata.framework_tags",
                            "Base": ", ".join(base_framework),
                            "Compare": ", ".join(compare_framework),
                        }
                    )

                base_caps = base_meta.get("capability_groups", []) or []
                compare_caps = compare_meta.get("capability_groups", []) or []
                if base_caps != compare_caps:
                    diff_rows.append(
                        {
                            "Field": "ai_metadata.capability_groups",
                            "Base": ", ".join(base_caps),
                            "Compare": ", ".join(compare_caps),
                        }
                    )

                if not diff_rows:
                    st.success(
                        "No differences found between the selected versions (for the tracked fields)."
                    )
                else:
                    st.markdown(
                        f"Showing differences between **v{base_version.version_number}** "
                        f"and **v{compare_version.version_number}**:"
                    )
                    st.table(diff_rows)

        st.markdown('</div>', unsafe_allow_html=True)

    # ---- OVERRIDES ----
    with tab_overrides:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Override History (Metadata)")

        overrides = repository.list_overrides_for_record(selected_record_id)

        if not overrides:
            st.info("No metadata overrides have been recorded for this use case yet.")
        else:
            override_rows = []
            for o in overrides:
                override_rows.append(
                    {
                        "Version #": next(
                            (v.version_number for v in versions if v.id == o.version_id),
                            "?",
                        ),
                        "Field": o.field_path,
                        "Original": ", ".join(o.original_value) if isinstance(o.original_value, list) else str(o.original_value),
                        "New": ", ".join(o.new_value) if isinstance(o.new_value, list) else str(o.new_value),
                        "Overridden By": o.overridden_by_name,
                        "Overridden At (Toronto)": o.overridden_at.strftime("%Y-%m-%d %H:%M"),
                    }
                )

            st.table(override_rows)

        st.markdown('</div>', unsafe_allow_html=True)



def main():
    """
    Main entry point for the app.
    """

    # 🔒 Force Dark theme only
    from core.styles import apply_theme
    apply_theme("Dark")

    # 1. Get the current user (from the sidebar dropdown)
    user = get_current_user()

    # Seed demo data only once per session
    if "demo_data_initialized" not in st.session_state:
        repository.ensure_demo_data(user_for_demo=user)
        st.session_state["demo_data_initialized"] = True

    st.sidebar.markdown(
        f"**Logged in as:**  \n{user.display_name}  \n`{user.role}`"
    )

    page = st.sidebar.radio(
        "Navigation",
        ["My Records", "Editor", "History"],
    )

    if page == "My Records":
        show_my_records(user)
    elif page == "Editor":
        show_editor(user)
    elif page == "History":
        show_history(user)


if __name__ == "__main__":
    main()

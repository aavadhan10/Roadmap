import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page config
st.set_page_config(
    page_title="Strategic Priorities Roadmap",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🗺️ Strategic Priorities Roadmap Timeline")
st.markdown("Interactive timeline view of our strategic AI tool priorities and implementation roadmap.")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your Excel file",
    type=['xlsx', 'xls'],
    help="Upload your AI Tool Request Pipeline Excel file to update the roadmap"
)

@st.cache_data
def load_and_process_data(uploaded_file):
    """Load and process the Excel data"""
    if uploaded_file is not None:
        # Read Excel file
        df = pd.read_excel(uploaded_file, sheet_name=0, header=2)
        
        # Clean up the dataframe
        df = df.dropna(subset=['Name'])  # Remove rows without names
        df = df[df['Name'].str.strip() != '']  # Remove empty names
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Fill missing values
        df = df.fillna('')
        
        # Process Quarter Date column to extract timeline info
        df['Timeline'] = df['Quarter Date'].astype(str)
        
        # Create a more detailed timeline mapping
        quarter_mapping = {
            'Q1 2025': '2025-03-31',
            'Q2 2025': '2025-06-30', 
            'Q3 2025': '2025-09-30',
            'Q4 2025': '2025-12-31',
            'Q1 2026': '2026-03-31',
            'Q2 2026': '2026-06-30',
            'Q3 2026': '2026-09-30',
            'Q4 2026': '2026-12-31'
        }
        
        df['End_Date'] = df['Timeline'].map(quarter_mapping)
        df['End_Date'] = pd.to_datetime(df['End_Date'], errors='coerce')
        
        # Create start dates (3 months before end date for quarterly items)
        df['Start_Date'] = df['End_Date'] - pd.DateOffset(months=3)
        
        # Status color mapping
        status_colors = {
            'Budget Evaluation': '#FFA500',  # Orange
            'Evaluating': '#87CEEB',         # Sky Blue
            'In Progress': '#32CD32',        # Lime Green
            'Completed': '#228B22',          # Forest Green
            'On Hold': '#FF6347',            # Tomato
            'Planning': '#9370DB',           # Medium Purple
            '': '#D3D3D3'                    # Light Gray for empty
        }
        
        df['Color'] = df['Status'].map(status_colors).fillna('#D3D3D3')
        
        # Priority mapping (assuming higher scores are higher priority)
        df['Priority_Numeric'] = pd.to_numeric(df['Total Priority Score'], errors='coerce')
        
        return df
    return None

# Load data
if uploaded_file:
    df = load_and_process_data(uploaded_file)
else:
    st.info("👆 Please upload your Excel file to see the roadmap timeline.")
    st.stop()

if df is None or df.empty:
    st.error("Could not load data from the uploaded file. Please check the file format.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Timeline filter
timeline_options = ['All'] + sorted(df['Timeline'].unique())
selected_timeline = st.sidebar.selectbox("Filter by Quarter", timeline_options)

# Status filter
status_options = ['All'] + sorted(df['Status'].unique())
selected_status = st.sidebar.multiselect("Filter by Status", status_options, default=['All'])

# Stakeholder filter
stakeholder_options = ['All'] + sorted(df['Requesting Stakeholder'].unique())
selected_stakeholder = st.sidebar.selectbox("Filter by Stakeholder", stakeholder_options)

# Apply filters
filtered_df = df.copy()

if selected_timeline != 'All':
    filtered_df = filtered_df[filtered_df['Timeline'] == selected_timeline]

if 'All' not in selected_status and selected_status:
    filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]

if selected_stakeholder != 'All':
    filtered_df = filtered_df[filtered_df['Requesting Stakeholder'] == selected_stakeholder]

# Main content
if not filtered_df.empty:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", len(filtered_df))
    
    with col2:
        budget_eval_count = len(filtered_df[filtered_df['Status'] == 'Budget Evaluation'])
        st.metric("Budget Evaluation", budget_eval_count)
    
    with col3:
        evaluating_count = len(filtered_df[filtered_df['Status'] == 'Evaluating'])
        st.metric("Evaluating", evaluating_count)
    
    with col4:
        in_progress_count = len(filtered_df[filtered_df['Status'] == 'In Progress'])
        st.metric("In Progress", in_progress_count)

    # Create timeline visualization
    st.subheader("📊 Timeline View")
    
    # Prepare data for Gantt chart
    gantt_data = []
    for idx, row in filtered_df.iterrows():
        if pd.notna(row['Start_Date']) and pd.notna(row['End_Date']):
            gantt_data.append({
                'Task': row['Name'][:50] + ('...' if len(row['Name']) > 50 else ''),
                'Start': row['Start_Date'],
                'Finish': row['End_Date'],
                'Resource': row['Requesting Stakeholder'],
                'Status': row['Status'],
                'Tool': row['Tool Name'],
                'Timeline': row['Timeline'],
                'Full_Name': row['Name']
            })
    
    if gantt_data:
        gantt_df = pd.DataFrame(gantt_data)
        
        # Create Gantt chart using plotly
        fig = go.Figure()
        
        # Group by stakeholder for color coding
        stakeholders = gantt_df['Resource'].unique()
        colors = px.colors.qualitative.Set3[:len(stakeholders)]
        color_map = dict(zip(stakeholders, colors))
        
        for idx, row in gantt_df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Start'], row['Finish'], row['Finish'], row['Start'], row['Start']],
                y=[idx, idx, idx+0.8, idx+0.8, idx],
                fill='toself',
                fillcolor=color_map.get(row['Resource'], '#1f77b4'),
                line=dict(color=color_map.get(row['Resource'], '#1f77b4'), width=2),
                name=row['Resource'],
                text=f"{row['Task']}<br>Status: {row['Status']}<br>Tool: {row['Tool']}",
                hovertemplate="%{text}<extra></extra>",
                showlegend=idx == 0 or row['Resource'] not in [gantt_df.iloc[i]['Resource'] for i in range(idx)]
            ))
        
        fig.update_layout(
            title="Strategic Priorities Timeline",
            xaxis_title="Timeline",
            yaxis_title="Projects",
            height=max(400, len(gantt_data) * 40),
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(gantt_data))),
                ticktext=[item['Task'] for item in gantt_data],
                autorange='reversed'
            ),
            hovermode='closest',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Status Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Status Distribution")
        status_counts = filtered_df['Status'].value_counts()
        if not status_counts.empty:
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Distribution by Status"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Stakeholder Breakdown")
        stakeholder_counts = filtered_df['Requesting Stakeholder'].value_counts()
        if not stakeholder_counts.empty:
            fig_bar = px.bar(
                x=stakeholder_counts.index,
                y=stakeholder_counts.values,
                title="Requests by Stakeholder"
            )
            fig_bar.update_layout(xaxis_title="Stakeholder", yaxis_title="Count")
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed table view
    st.subheader("📋 Detailed View")
    
    # Select columns to display
    display_columns = ['Name', 'Requesting Stakeholder', 'Timeline', 'Tool Name', 'Status', 'Total Priority Score']
    display_df = filtered_df[display_columns].copy()
    
    # Style the dataframe
    def highlight_status(row):
        colors = {
            'Budget Evaluation': 'background-color: #FFF3CD',
            'Evaluating': 'background-color: #D1ECF1', 
            'In Progress': 'background-color: #D4EDDA',
            'Completed': 'background-color: #C8E6C9',
            'On Hold': 'background-color: #F8D7DA',
            'Planning': 'background-color: #E2D9F7'
        }
        status_color = colors.get(row['Status'], '')
        return [status_color] * len(row)
    
    styled_df = display_df.style.apply(highlight_status, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Quick stats
    st.subheader("📊 Quick Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Quarterly Distribution:**")
        quarter_dist = filtered_df['Timeline'].value_counts().sort_index()
        for quarter, count in quarter_dist.items():
            st.write(f"• {quarter}: {count} items")
    
    with col2:
        st.write("**Top Tools:**")
        tool_counts = filtered_df[filtered_df['Tool Name'] != '']['Tool Name'].value_counts().head(5)
        for tool, count in tool_counts.items():
            st.write(f"• {tool}: {count} requests")
    
    with col3:
        if 'Priority_Numeric' in filtered_df.columns:
            priority_df = filtered_df.dropna(subset=['Priority_Numeric'])
            if not priority_df.empty:
                st.write("**Priority Insights:**")
                avg_priority = priority_df['Priority_Numeric'].mean()
                high_priority = len(priority_df[priority_df['Priority_Numeric'] > avg_priority])
                st.write(f"• Average Priority: {avg_priority:.1f}")
                st.write(f"• High Priority Items: {high_priority}")

else:
    st.warning("No data matches your current filter selection. Please adjust the filters.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Update this roadmap by uploading a new Excel file with the same structure.")
st.markdown("🔄 **Last updated:** " + datetime.now().strftime("%Y-%m-%d %H:%M"))

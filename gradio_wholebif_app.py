# gradio_wholebif_app.py – v3.0
# Full-featured UI (autocomplete, pair search, heat‑map)
# Requires: gradio, sqlalchemy, pandas, rapidfuzz, pillow, numpy

import os, io, asyncio
from functools import lru_cache

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from rapidfuzz import process, fuzz
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, sessionmaker, mapped_column

import gradio as gr

# ORM --------------------------------------------------------------------
class Base(DeclarativeBase): pass

class Circuit(Base):
    __tablename__ = "Circuits"
    circuit_id = mapped_column(sa.Text, primary_key=True)
    names      = mapped_column(sa.Text)

class Connection(Base):
    __tablename__ = "Connections"
    id            = mapped_column(sa.Integer, primary_key=True)
    circuit_id    = mapped_column(sa.Text)
    receiver_id   = mapped_column(sa.Text)
    connection_flag = mapped_column(sa.Boolean)

class Reference(Base):
    __tablename__ = "References"
    reference_id = mapped_column(sa.Text, primary_key=True)
    doi          = mapped_column(sa.Text)
    bibtex       = mapped_column(sa.Text)

class Evidence(Base):
    __tablename__ = "Evidence"
    id            = mapped_column(sa.Integer, primary_key=True)
    connection_id = mapped_column(sa.Integer)
    description   = mapped_column(sa.Text)

class Score(Base):
    __tablename__ = "Scores"
    id            = mapped_column(sa.Integer, primary_key=True)
    connection_id = mapped_column(sa.Integer)
    cited_score   = mapped_column(sa.Float)
    extracted_correctly = mapped_column(sa.Float)
    experimental_match  = mapped_column(sa.Float)

# DB ---------------------------------------------------------------------
DB_URI = os.getenv("WHOLEBIF_DB_URI", "sqlite:///wholebif.db")
engine = sa.create_engine(DB_URI, future=True)
Session = sessionmaker(engine, expire_on_commit=False)

# Helpers ----------------------------------------------------------------
@lru_cache(maxsize=None)
def circuits_df():
    with Session() as s:
        return pd.read_sql(sa.select(Circuit.circuit_id, Circuit.names), s.bind)

@lru_cache(maxsize=None)
def connections_df():
    with Session() as s:
        return pd.read_sql(sa.select(Connection.circuit_id,
                                     Connection.receiver_id,
                                     Connection.connection_flag), s.bind)

def prefix_candidates(prefix: str, limit: int = 20):
    if len(prefix) < 2:
        return []
    df = circuits_df()
    p = prefix.lower()
    mask = df.circuit_id.str.lower().str.startswith(p) | df.names.str.lower().str.startswith(p)
    return df[mask].circuit_id.head(limit).tolist()

def fuzzy_candidates(q: str, limit: int = 12, cutoff: int = 60):
    choices = circuits_df().set_index("circuit_id")["names"].to_dict()
    ranked = process.extract(q, choices, scorer=fuzz.WRatio, limit=limit)
    return [cid for cid, sc, _ in ranked if sc >= cutoff]

async def search_single(q: str):
    ids = fuzzy_candidates(q)
    if not ids:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    async with Session() as s:
        conns = pd.read_sql(sa.select(Connection).where(Connection.circuit_id.in_(ids)), s.bind)
        keys  = conns.id.tolist()
        refs  = pd.read_sql(sa.select(Reference).join(Connection, Reference.reference_id == Connection.reference_id).where(Connection.id.in_(keys)), s.bind)
        evid  = pd.read_sql(sa.select(Evidence).where(Evidence.connection_id.in_(keys)), s.bind)
        scores= pd.read_sql(sa.select(Score).where(Score.connection_id.in_(keys)), s.bind)
    return conns, refs, evid, scores

async def search_pair(circ: str, recv: str):
    async with Session() as s:
        conn = s.scalar(sa.select(Connection).where(Connection.circuit_id == circ,
                                                    Connection.receiver_id == recv,
                                                    Connection.connection_flag == True))
        if conn is None:
            return False, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        cdf   = pd.read_sql(sa.select(Connection).where(Connection.id == conn.id), s.bind)
        refs  = pd.read_sql(sa.select(Reference).join(Connection).where(Connection.id == conn.id), s.bind)
        evid  = pd.read_sql(sa.select(Evidence).where(Evidence.connection_id == conn.id), s.bind)
        scores= pd.read_sql(sa.select(Score).where(Score.connection_id == conn.id), s.bind)
    return True, cdf, refs, evid, scores

# Heat‑map ---------------------------------------------------------------
CELL = 20
COLOR_ON  = (63, 81, 181)
COLOR_OFF = (255, 255, 255)
GRID      = (209, 213, 219)
@lru_cache(maxsize=8)
def build_heatmap():
    df_conn = connections_df()
    circuits = sorted(pd.unique(df_conn[['circuit_id','receiver_id']].values.ravel()))
    n = len(circuits)
    idx = {cid:i for i,cid in enumerate(circuits)}
    mat = np.zeros((n,n), dtype=bool)
    for _,r in df_conn.iterrows():
        if r.connection_flag:
            mat[idx[r.circuit_id], idx[r.receiver_id]] = True
    img = Image.new('RGB', (CELL*n, CELL*n), COLOR_OFF)
    d = ImageDraw.Draw(img)
    for i in range(n):
        for j in range(n):
            x0,y0 = j*CELL, i*CELL
            x1,y1 = x0+CELL, y0+CELL
            if mat[i,j]:
                d.rectangle([x0,y0,x1,y1], fill=COLOR_ON)
            d.rectangle([x0,y0,x1,y1], outline=GRID)
    buf = io.BytesIO(); img.save(buf, format='PNG')
    return buf.getvalue()

# Callbacks --------------------------------------------------------------
def cb_prefix(txt): return gr.Dropdown.update(choices=prefix_candidates(txt))
def cb_suggest(sel): return gr.Textbox.update(value=sel)
def cb_single(q): return asyncio.run(search_single(q))
def cb_pair(c,r): ok,cdf,rf,ev,sc = asyncio.run(search_pair(c,r)); return ('✅ Found' if ok else '❌ None'), cdf, rf, ev, sc
def cb_matrix(_): return gr.Image.update(value=build_heatmap())

# UI ---------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Soft(primary_hue=\"indigo\")) as demo:
    gr.Markdown(\"## WholeBIF Explorer – Postgres/SQLite UI\")
    with gr.Tab(\"Single\"):
        kw = gr.Textbox(label=\"Keyword\"); sug = gr.Dropdown(choices=[]); run = gr.Button(\"Search\")
        kw.change(cb_prefix, kw, sug, debounce=0.05); sug.change(cb_suggest, sug, kw)
        conn = gr.Dataframe(); ref = gr.Dataframe(height=200); ev = gr.Dataframe(height=200); sc = gr.Dataframe(height=200)
        run.click(cb_single, kw, [conn, ref, ev, sc])
    with gr.Tab(\"Pair\"):
        df = circuits_df(); ids = df.circuit_id.tolist()
        c = gr.Dropdown(label=\"Circuit\", choices=ids, filterable=True)
        r = gr.Dropdown(label=\"Receiver\", choices=ids, filterable=True)
        run2 = gr.Button(\"Check\")
        status = gr.Markdown(); cd = gr.Dataframe(); rf2 = gr.Dataframe(); ev2 = gr.Dataframe(); sc2 = gr.Dataframe()
        run2.click(cb_pair, [c,r], [status, cd, rf2, ev2, sc2])
    with gr.Tab(\"Matrix\"):
        img = gr.Image(value=build_heatmap()); gr.Markdown(\"Heat‑map of all recorded connections.\")
        gr.Button(\"Refresh\").click(cb_matrix, None, img)
if __name__ == \"__main__\":
    demo.queue().launch(server_port=int(os.getenv(\"PORT\", 7860)))

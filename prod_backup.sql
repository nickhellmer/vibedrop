--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Postgres.app)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: vibedrop_prod_db_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO vibedrop_prod_db_user;

--
-- Name: feedback_enum; Type: TYPE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TYPE public.feedback_enum AS ENUM (
    'like',
    'neutral',
    'dislike'
);


ALTER TYPE public.feedback_enum OWNER TO vibedrop_prod_db_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO vibedrop_prod_db_user;

--
-- Name: circle_memberships; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.circle_memberships (
    id integer NOT NULL,
    user_id integer NOT NULL,
    circle_id integer NOT NULL,
    joined_at timestamp without time zone NOT NULL
);


ALTER TABLE public.circle_memberships OWNER TO vibedrop_prod_db_user;

--
-- Name: circle_membership_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.circle_membership_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.circle_membership_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: circle_membership_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.circle_membership_id_seq OWNED BY public.circle_memberships.id;


--
-- Name: drop_creds; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.drop_creds (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_likes integer NOT NULL,
    total_dislikes integer NOT NULL,
    total_possible integer NOT NULL,
    drop_cred_score double precision NOT NULL,
    computed_at timestamp with time zone NOT NULL,
    score_version smallint NOT NULL,
    params jsonb,
    window_label character varying(32),
    window_start timestamp with time zone,
    window_end timestamp with time zone
);


ALTER TABLE public.drop_creds OWNER TO vibedrop_prod_db_user;

--
-- Name: drop_creds_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.drop_creds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.drop_creds_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: drop_creds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.drop_creds_id_seq OWNED BY public.drop_creds.id;


--
-- Name: song_feedback; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.song_feedback (
    id integer NOT NULL,
    user_id integer NOT NULL,
    song_id integer NOT NULL,
    feedback character varying(10) NOT NULL,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.song_feedback OWNER TO vibedrop_prod_db_user;

--
-- Name: song_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.song_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.song_feedback_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: song_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.song_feedback_id_seq OWNED BY public.song_feedback.id;


--
-- Name: sound_circles; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.sound_circles (
    id integer NOT NULL,
    circle_name character varying(100) NOT NULL,
    drop_frequency character varying(20) NOT NULL,
    drop_day1 character varying(20),
    drop_day2 character varying(20),
    drop_time timestamp with time zone NOT NULL,
    invite_code character varying(10),
    creator_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.sound_circles OWNER TO vibedrop_prod_db_user;

--
-- Name: sound_circle_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.sound_circle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sound_circle_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: sound_circle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.sound_circle_id_seq OWNED BY public.sound_circles.id;


--
-- Name: submissions; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    circle_id integer NOT NULL,
    user_id integer NOT NULL,
    spotify_track_id character varying(100) NOT NULL,
    cycle_date date NOT NULL,
    submitted_at timestamp with time zone NOT NULL,
    visible_to_others boolean
);


ALTER TABLE public.submissions OWNER TO vibedrop_prod_db_user;

--
-- Name: submission_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.submission_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.submission_id_seq OWNED BY public.submissions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    spotify_id character varying(128) NOT NULL,
    vibedrop_username character varying(64) NOT NULL,
    display_name character varying(128),
    email character varying(128),
    access_token character varying(1024) NOT NULL,
    refresh_token character varying(1024),
    expires_at timestamp without time zone,
    drop_cred double precision,
    created_at timestamp without time zone NOT NULL,
    sms_notifications boolean,
    phone_number character varying(20)
);


ALTER TABLE public.users OWNER TO vibedrop_prod_db_user;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.user_id_seq OWNED BY public.users.id;


--
-- Name: vibe_scores; Type: TABLE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE TABLE public.vibe_scores (
    id integer NOT NULL,
    user1_id integer NOT NULL,
    user2_id integer NOT NULL,
    vibe_index double precision NOT NULL,
    last_updated timestamp without time zone NOT NULL
);


ALTER TABLE public.vibe_scores OWNER TO vibedrop_prod_db_user;

--
-- Name: vibe_score_id_seq; Type: SEQUENCE; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE SEQUENCE public.vibe_score_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vibe_score_id_seq OWNER TO vibedrop_prod_db_user;

--
-- Name: vibe_score_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER SEQUENCE public.vibe_score_id_seq OWNED BY public.vibe_scores.id;


--
-- Name: circle_memberships id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.circle_memberships ALTER COLUMN id SET DEFAULT nextval('public.circle_membership_id_seq'::regclass);


--
-- Name: drop_creds id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.drop_creds ALTER COLUMN id SET DEFAULT nextval('public.drop_creds_id_seq'::regclass);


--
-- Name: song_feedback id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.song_feedback ALTER COLUMN id SET DEFAULT nextval('public.song_feedback_id_seq'::regclass);


--
-- Name: sound_circles id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.sound_circles ALTER COLUMN id SET DEFAULT nextval('public.sound_circle_id_seq'::regclass);


--
-- Name: submissions id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.submissions ALTER COLUMN id SET DEFAULT nextval('public.submission_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: vibe_scores id; Type: DEFAULT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.vibe_scores ALTER COLUMN id SET DEFAULT nextval('public.vibe_score_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.alembic_version (version_num) FROM stdin;
94be691cd5eb
\.


--
-- Data for Name: circle_memberships; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.circle_memberships (id, user_id, circle_id, joined_at) FROM stdin;
1	2	1	2025-08-08 03:18:30.271732
2	3	1	2025-08-08 03:19:32.516853
3	4	1	2025-08-08 03:29:09.158088
4	5	1	2025-08-08 03:33:17.143018
5	6	1	2025-08-08 14:56:52.410699
6	7	1	2025-08-08 14:59:04.205912
7	8	1	2025-08-08 15:18:45.865796
8	9	1	2025-08-09 15:51:45.75625
9	10	1	2025-08-10 22:39:00.263279
10	2	2	2025-08-12 19:26:58.746189
11	10	2	2025-08-12 19:38:36.444158
12	12	2	2025-08-12 21:57:17.918758
13	2	3	2025-08-12 23:02:14.837912
14	2	4	2025-08-13 01:43:18.712832
15	2	5	2025-08-13 03:12:06.07658
16	13	5	2025-08-13 03:20:49.653947
17	14	1	2025-08-13 13:07:56.044041
18	15	1	2025-08-13 18:42:45.297307
19	16	2	2025-08-15 03:33:37.054467
20	17	1	2025-08-15 20:33:13.291367
21	18	1	2025-08-15 20:42:03.042995
22	18	2	2025-08-15 20:45:13.29442
\.


--
-- Data for Name: drop_creds; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.drop_creds (id, user_id, total_likes, total_dislikes, total_possible, drop_cred_score, computed_at, score_version, params, window_label, window_start, window_end) FROM stdin;
\.


--
-- Data for Name: song_feedback; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.song_feedback (id, user_id, song_id, feedback, "timestamp") FROM stdin;
1	2	1	like	2025-08-11 21:04:24.097507
2	2	2	like	2025-08-11 21:04:34.766481
3	2	6	like	2025-08-11 21:04:57.828092
4	2	7	like	2025-08-11 21:05:01.91933
5	2	4	dislike	2025-08-12 23:02:45.899798
6	7	7	like	2025-08-13 13:17:09.558512
7	13	18	like	2025-08-13 20:12:08.031569
8	2	22	like	2025-08-13 20:44:09.291001
9	10	7	dislike	2025-08-13 22:18:25.755043
10	5	2	like	2025-08-15 14:12:45.647892
11	17	28	like	2025-08-15 21:42:02.841886
\.


--
-- Data for Name: sound_circles; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.sound_circles (id, circle_name, drop_frequency, drop_day1, drop_day2, drop_time, invite_code, creator_id, created_at) FROM stdin;
1	JOIN THIS CIRCLE (Weekly 5pm EST) - Global Circle for All Testers	Weekly	Friday	Monday	2025-08-08 21:00:00+00	KcieU5EX	2	2025-08-08 03:18:30.262062
2	Mad Lads of the Midwest	Weekly	Friday	Monday	2025-08-12 21:00:00+00	mcF3dFFZ	2	2025-08-12 19:26:58.735556
3	SOLO TEST - Daily 8pm est	Daily	Monday	Monday	2025-08-13 00:00:00+00	dik72Zwr	2	2025-08-12 23:02:14.832293
4	SOLO TEST - Daily 10pm est	Daily	Monday	Monday	2025-08-14 02:00:00+00	6bglm4Zs	2	2025-08-13 01:43:18.705345
5	Sophia's Circle - Wednesdays 1PM EST	Weekly	Wednesday	Monday	2025-08-13 17:00:00+00	mCIz0W94	2	2025-08-13 03:12:06.063166
\.


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.submissions (id, circle_id, user_id, spotify_track_id, cycle_date, submitted_at, visible_to_others) FROM stdin;
1	1	3	6kIUGrML374os1R2qC1jji	2025-08-01	2025-08-08 03:19:59.037981+00	f
2	1	6	3PczYtUqSoEXhXQlzbMDIG	2025-08-01	2025-08-08 14:57:27.827668+00	f
3	1	7	2E0bqoMlIb2xmFyZHRjtzK	2025-08-01	2025-08-08 15:00:33.20959+00	f
4	1	8	37jTPJgwCCmIGMPB45jrPV	2025-08-01	2025-08-08 15:19:42.372716+00	f
5	1	2	7H3bWxgjLiSnwStlBGgAlG	2025-08-01	2025-08-08 18:30:10.504554+00	f
6	1	4	4waPZF96vX1Oz5pzH6dB0h	2025-08-01	2025-08-08 18:45:53.621511+00	f
7	1	5	0cFlXjTxFdMGGPfLVpt3Wv	2025-08-01	2025-08-08 19:09:21.179417+00	f
8	1	8	6G1Mz5yMgn0ydOlIvTrZ65	2025-08-08	2025-08-09 13:57:42.91756+00	f
9	1	6	7itHyuODr4R7Fdz454zn3F	2025-08-08	2025-08-09 20:14:55.393894+00	f
10	1	9	7B3BwNecBhKvNwSMOOl7Gk	2025-08-08	2025-08-09 21:35:42.691192+00	f
11	1	10	3BpHUFGTW8KGd7FLEQJ4ac	2025-08-08	2025-08-11 00:39:32.4609+00	f
12	2	10	3BmjRmFTESgWZLPSVGp8aG	2025-08-09	2025-08-12 19:39:20.645487+00	f
13	2	12	3vRYtf5xgPrYeVzAmqvzTd	2025-08-09	2025-08-12 21:58:15.24398+00	f
14	3	2	7MkABWMLDrvbW7ukxGwPTE	2025-08-12	2025-08-12 23:02:29.273255+00	f
15	2	2	7f1ZaX67foF2snj6Paix0L	2025-08-09	2025-08-12 23:06:23.838389+00	f
16	4	2	7gyEo8okigsNt9Nn2ArUWR	2025-08-12	2025-08-13 01:43:36.684919+00	f
17	1	2	6iTAtdjDzH8f3D1KcASfQQ	2025-08-09	2025-08-13 02:12:21.768757+00	f
18	5	2	5AQuUEnrfiGM3dfUBTIutY	2025-08-06	2025-08-13 03:13:18.000111+00	f
19	1	14	1136gMPQlMTz2OZo32xowc	2025-08-09	2025-08-13 13:14:02.058151+00	f
20	1	4	2KaA0Tgl3RmQLzcvLEtzLH	2025-08-09	2025-08-13 13:16:41.401287+00	f
21	1	3	1LOFK4zdpDABD2mmT5wRKH	2025-08-09	2025-08-13 14:09:36.260065+00	f
22	5	13	2SsY5k7UWFqgye3PUMG3Oq	2025-08-06	2025-08-13 14:10:40.75948+00	f
23	1	15	3ld1FzyNgpZwGn4h9cOXrq	2025-08-09	2025-08-13 18:43:43.644445+00	f
24	5	2	5HQtRirC8ERASUifigbapJ	2025-08-13	2025-08-14 13:22:08.435487+00	f
25	1	6	2Asiem9O0YGuvvoAkz8aSq	2025-08-08	2025-08-14 20:37:02.507322+00	f
26	2	16	15VRO9CQwMpbqUYA7e6Hwg	2025-08-08	2025-08-15 03:34:21.101197+00	f
27	1	7	3QcZ0HiwWxwQYT2F17DCTm	2025-08-08	2025-08-15 14:06:35.942253+00	f
28	1	5	3fPW4EhpRR6BwLRPDThNeg	2025-08-08	2025-08-15 14:13:50.537058+00	f
29	1	17	3LXxHFZWt6OHdBsgucSIjJ	2025-08-08	2025-08-15 20:34:01.146784+00	f
30	1	18	3B7ww7BtZcb2MD46JiQuqt	2025-08-08	2025-08-15 20:43:33.989319+00	f
31	2	18	1UGD3lW3tDmgZfAVDh6w7r	2025-08-08	2025-08-15 20:46:04.449547+00	f
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.users (id, spotify_id, vibedrop_username, display_name, email, access_token, refresh_token, expires_at, drop_cred, created_at, sms_notifications, phone_number) FROM stdin;
8	jacksonsoccer3	Sean Jackson	\N	\N	BQC9nWYsBW0o91sSXj8REF5AlXbhou39R-4kpuEIPRQd3F8OtemZd7G4qVRmT17g07Bfg0PuwEuJgNe7Zntr8Sz-EeFJfhp94K4ZdpO4A7oe3AH1sqOUb9ozWIWSU0SUUryF1HMZ760aK0wOPN9GM7Rm1yi2-l03djH575YZQsKPdSxT1RG4lZ3irypwDMZRJzKapv3w1EuwJDJ2M_j_gwkDhESL9grQUVU2R1gdrT1R0SyOfidIqaeFVE2pfrBOTn7MQ-93Wb_wbYSotDGm-m5xplqpiNs3m34Lg0E	\N	\N	5	2025-08-08 15:18:06.357844	t	\N
4	jpbollman-7	Long Dong Silver	\N	\N	BQDCs78FujfTWLxCACc-VtqP5IrS0XtLXm_cjs4Au-Mq8_iuiKu4mNG0jExQw99ThHSgQLWjrDwsZLNOy5zeG6T4xdvXsELZFYO0aGEvPtTcCl-vCe-t8Vl2UKOcexflvlHO4FFcpccsGgob5m6NWeqVQv_2ZfZAu_SOWHddQSgJePnip9UBeFaJqt5Glxu97oLVRz_v-vKbLNfYsk-SFaRx5zJI8r_bZcX3-LVSrpJ0fzgDVxVw27DHwkHx8NkcWzIWSjEFgLt_qmW2uLwP1Ej8Mdh_xJs	AQBE4aIznhEM2sTZBntH1EiSnjZo6aStU4IL1ATixkx4MEpp0PLbJzxEgUuMS0H_dDMZ4WcHL1s_7vGqmwkY60yeU9c_NexgU2ys4sXpmM7i11IgucrDIo42eowBbnj_1lU	2025-08-15 15:23:51.985875	5	2025-08-08 03:28:14.126097	t	\N
14	reddevilfc98	AP123	reddevilfc98	\N	BQBpw8DyJrSwrExaD5Evwo7L8OzJxAjKgHAbprkx1Uwwrnn6cbbp510E1ugvtEpHSCDoUQdbFnxZK2k1IFjoN2wF63asMve1TVAjUrBkyGe3BgyEnFK8WW3c_wQ5NpDQ9_sXCqi2JH0KfaATUH0lF_nwcXOD6_nCwnHapmOaS_2R_7I5q91p3008g3MSVf04UUxvHvgUA0pDZ3kLcXMDMNwa49Xv0CDlCk-Td3n0rxlfeRmKB0GsrS2YZA4bzBY5hzmPqJ4_C_GrgbWskUG_CkUiQdXKWgL56JV-	AQCSLlp1nDdmfiuhrIcb3A6AMCmxzWWd9xmgw5zWLOuRTK-jecqXweeZmSrweArn9l5Q51SqkrsQVKNd83rT9pyMh2lROr4oJxIIVRcFl--TLI5nKfAgYmtKDaBmk2PKZ-8	2025-08-13 14:06:29.326032	5	2025-08-13 13:06:29.552428	t	\N
9	1284945354	spideytingz	\N	\N	BQB0mBgdp0a0EEPbUEctDUmmSvjgLNJ_24ohOSqIhKUfJCtqCJmGqALv96IEZDzXJL6Dxl3PFQKGI4ugcyN1DBXly-09XJaQGofeNJWaALFQZMqpS-KHuNVQRJmQADwFUE28YKmx6DDGNW9a0YDILOYX6Ef3E4RUytbJFOI0p1DHCsmoivendCDccIUCeYa1CY9_kwYo-iruKtu-qC0SyTuCB-mlRnSqDjuTLAChvnF-Pt_8cbRHOIB-YZrllSUHMfZTeIfhOFr73yX8zR0ekeeEGcc3WQXeQQ	\N	\N	5	2025-08-09 15:44:20.643536	t	\N
11	1295969724	 	\N	\N	BQCwTXpUyn2z96-ovLumt5pFf4NZt4nAd3Vgmllivbpc7BVUOD3wTnuQpq3ein-YxbrSh1LyrXme0GNaBR8LgEvoc6y-uRqGyTF9JOQ_0uFSAzsngYxBx1l_Ghs-LTXcuiP_Fi26hPhzMPaGP26Lb1ClwyHJShe3SXk4iOUf6HGA0DS-twlGtVfD6fl-tWdku4BbEf7yIQh8bN1T_u6l-IS73rl9Lb-Vp-69IKVi6SDKUKUqPHzd0UmUmkMvV1ZnaEeBn6m7ml8RePOXEEeWJ2caAnNpDlz5ZQ	\N	\N	5	2025-08-11 02:07:21.743037	t	\N
12	dkip456	Dkip456	Daniel Kipnis	\N	BQBfniM_Bc4mTbyXTUMaBO3osxdGWgkIB_M8Fw6zo4es1KfpDsb1i3EXRWWSbSFyVbMsTNUJyfYJLWEfs1hjCeDKiitRb0tSix2erhd8wm7Ozuo2qdgd8luEh73iiwwxBsKMJE0Rm9_o8DjYfzUR2mrD-qcBdVeYZ9qPcalrUYsoYo2jd9sfwEh9IXAIzzAcz1SnGkOjheSAz_sUJ1cS6bJssmPU83IZL1UZ_mt3Ti8FoyzL2LFSFZh6HNAH6oTWV8QYfSNRYO9wI1eZ4tnRI2qz2U_-rA	AQBQah1qm8Nf3Omohm-XRVLmdF0U0mfl-ZM5GBq-gSiAtbIreIqUysKUIUhKbHeDNi5iSXYv0VNf0s7kZoa9b1ZvGv4mCeW_js0RxX3lLUpSOUBQuuZi6xh0pMZhCrNpqto	2025-08-12 22:56:20.155719	5	2025-08-12 21:56:20.28573	t	\N
13	sophiad187	Sophiahd	sophiad187	\N	BQDGAVNFI2HUISVAj-X0K3YLtf2kltNzmucwxMVqxSG1q1020nynAymIAPCOO_C9_Nfj2wwX05xQJV5Wfh7d2CNgcOPneQeFUwnWspbE_VqlxxPBZv_TqcQwhMc044E3eDnFFvRf03MhiVcalW5NsW9VaoNj3vUbDxCDriimLi5nE2KxsXEyift1Vf701_84kYwKEev6yKALny1qp0ZF33hBaI1UfjaTh24NhRMHuZTchIF6QgYgJpiGgPGqVSyUmeClMfR73NDZVIDDAup4nNhuhyskx4BAww	AQDd_Abw-5pIiwglxtu0TU1wi-yGnW5E0g1KgG8mNHM30VM8qpImWNU-muWpQl26438p9uoAykfivbeiD5eJnohlNbkp_bs4N4elXGHsQZmDiQKG9QMFKWBP5cDB7JAkh5E	2025-08-13 04:30:24.909976	5	2025-08-13 03:20:03.004804	t	\N
7	asj3-us	Potus530	\N	\N	BQDOOma6nFLg1yWsSbCrEN_vHiUCiWx1iY3A1634ojEwcnCAlZ2VKVysvrCLpWRpgOZbVI3X4eXqPc4ZU5dkkXODOW1WglnzmvE055LM_ewpuJs1Pnwn7RoyeVYMjfTHOQuPPnnxJ_cO-QJK-st8sDFO7QCnGI1k3bSxH958hPl1ubG0QbRUmckmwe3fK72AgNxt3XPnSWqMX51bxUgcevFpNprohDT5Bz_REtzaRkJlbbV5wKt1RRbs_LQoDaoq8BYEi9NISRXt2cu88qdRqvODPkWDEw	AQCRuwEIAQ2HjRpsZEei8nj7Iw_lbDMux6eL7kteiEFiZWEuRacHV4jVBagKurdBW5kR-KChyC7GtcpqUlBjzvwEAeNN-4EPeX4B4urFLZ8RDARD6CMNMYp0BgwHrOgKW0o	2025-08-15 15:06:19.212721	5	2025-08-08 14:58:47.120189	t	\N
15	22eau5go5kdqasaop4zhp5aia	sidgoesboo	Sidney Johnson	\N	BQCH6BAdr8X5QsEZdn8UvKNLpia6KBrDi_XUO5Eluw5n9BBhhNSW2-5B33_OwcMjVwT_CQ4NaAoIt9V9Ivgi2q09z980ZfjIMXoc0xbIq2X8uuEfCyzoDfx4vt1mX4X6Qbm_8pGagAgVhjgAQhDlOL4XmqGIfxaY7kwXCzmPeGmlm5UFQ0QAZmo1szjEzTDfgLOpT601nIYcM15M7Ff76ppmEdQvCMZRaKlvsKtZlxyY4sRU_RpUcpX5Pr0gXHS1E9GoCRV0z7N-X-3TVddiblEqxjEt3q2Xn6EXtX4b9soMqGyerjWvAw	AQCx92vQdEL43YvF7ufz202IkM2UekWKQjc0dJcC24J0ODYv-qhe75sfWfMdHxX3aUUyJ_cbpbWvu_Uu-kelOEd-rx5032mINLplk0iJ77VeS4BNnmFQ4ova5jf7n1LX7rE	2025-08-13 19:50:52.580206	5	2025-08-13 18:42:03.414317	t	\N
10	1261267687	D Rizz	\N	\N	BQD-K4_S6FT7Xy1APu_-HL4k6NsutGmneDoP8oWXXqv3SfHSigZZ0hqWvroc2LucA6IJQrGMOphDYeADPEspp5BDIpVD7bzCn4PWXkZFB4fRDn1Jz2bfNAbIyopRCpLKOvJxfsEif7_is2UtZJ-koUfrpxa9QxYRoyezgnYAPztyX1Bs1PmdVa7LCRgxnwwxRkUrHEO4mWzRYspDU9__yeOLz9g9_tM2yUAXlfINm3o12hklBM5wH8rcD1J1Yc5CSnaJpz6b1q9Q3C7vwyFx7bHy8LkEh6HUdg	\N	\N	5	2025-08-10 22:38:34.425909	t	\N
6	p51av8r	greatloop	\N	\N	BQBW39niCXzviROFj9c9_rZqUh5TCdj-NL8obn6BTYqKSKgWQf8PnRU_25lQzilTW2WWnoscJteAgM81PNzobu9Nj6xddewpVeb3ric_I5uZvsTtITz4UnkCqh2bXCaaBrJ2ap2kViJHggD_fdpFnzTXowgZuS0pQfE1drQh33HW9yGMLY-x5KjC_nN3r2mUykJg7n6q0ILQgR7_my82XcpCalwTTpKBaP3dzaiRwz9YlFfp1xeZi3fajVF-sy283CvRJqZFqsu-JJ8scT0Za9jNeQZGwA	AQBEEPJFxQh0v5qwMVKpk5T-Tmux59BUlytISNob2ssrbgy3RivsiSsPbTPZitPclsSVpQrtkKj51vJ0bWK3rCAvP6yii12tg-mCAUtWZg0-A81aD6KAqyLU_i_2Mh_T8XM	2025-08-14 16:27:19.50899	5	2025-08-08 14:56:46.554743	t	\N
16	1164346292	choi	RC	\N	BQBM2VWr6hwaWEzcdiaIV8UUaiurdpm-9F-0Ci8fv8vbni2ufYA68VVNpnKC_Tgr5Tr9MqRpgDlYofAJ8iqLJKuRb4qGuwr0-92zyZ4FgZEFLHaWMPI9vOobsxPzP42gi5E0uY6oIJ10bYIIFt8w04ZUNrYL3WG1-9Rm7bm3M8Y_g9i0UgDaEYK65P7MOxQqItW30aH229-6JR1jzpYqDq0ivys3SoG1IzlhGMB0FtC7DF1S4lGkKlhSWu9keQ6xQmyrl5sCi3qqy8JgaBF2XSJUObMaZmTfZw	AQAMqb65Y529rXsr1Wzu9fCaujjRMts5RmfHHxOSaFCuGLVS_gAlAwaQwuuHZM0YqeIMntm8FVlNxn-Zl9NmLfRXiEGIu9BOBzvP1ykvnXasv_EdHM3qNVjuCYdX50Jb4RM	2025-08-15 04:32:33.303223	5	2025-08-15 03:32:33.514576	t	\N
3	trent_wheeler	trent_wheeler	\N	\N	BQD5lDxdWxpWY8qIre4Z2Oj_nj59hflsNhkUWca-xpDEBCc84He4B_7eBpC-W_Ul9R36PhVqWINAqofO6pBXU9cKS4BEJZNk4P2PrPWHNGJ1SiL5hPnCTTZ-pWPBHJtBQH0OSB4t_5zpBXJcN_T3Y0dLnHJrtVcbpZYaMXuVsX4bmgdTp9VIccXQLjM5j0fmAZBLimyQZfXcLn9UVFfRamkz5liYyp-noccD9z9fj-NRvTstnM9oLsfK8sRNe_uJ93-Vu2kOYf5ZXJUoAERiY6W-pGX28fiYAh5GFg	AQAEp78VGIZQs6Jte6cJTzRgQ2vuAyxgcVrpw5EF24tWrfnpFXd0RzeWo00F7jTieskItU5xfXUwv4YW0ZnrvGDfu_AO0NAfpDhPcg9vU5QSav9AtA12z7PpsKehE5V8pRg	2025-08-15 17:53:29.594659	5	2025-08-08 03:19:25.848961	t	12173725755
2	7xw4yczo4i8q0fjnd2ytyu5fd	nickhellmer	\N	nhellmer25@gmail.com	BQAF1FTKsrJ83IGatuta60zD4kMCbcqgJ_1rZUlf5ZajVygeJTTNgTBpd4uIe-06Kw5skqut21iPk3wJORkxO7ect3fA55ZjZ00bch04vzhy9ReYQSocpp9oAOpDI7pAUjcAmcF6DeT974QrTg33haGRZeGsvAaNQffzZsPfLkYcUD7e8gOBiLAP6ZeRhEhXAn1WEsxBFlLqzinFRHyACzvuiGQKtnu2hrYaSUoHlqf_Yh1n6ZEOmT4f5RbEfv9NqBpokHfxGwdtYSfECNjWi1Z5Ni8YXDnG5Rl7TSxuY9Ng5ZpMEXsByg	AQB95bWv56WrALy4NBmUyEwaGQu43W2gFMrvRARB7bOtQjtmFdl8Mq9jwtXc9Ri1hLNo9iMK8qx3xzydbPq8m9YK6CCzV_sy2FjoH08qXzjGKraLC3cAV_hcJOa7hAL2RJY	2025-08-15 21:21:28.060362	5	2025-08-08 03:16:59.858104	t	12174174120
5	zorw3yxp5oq6d0lhnn1mpshev	Cartier	\N	\N	BQC6ugP0I212FjKJ-m2eyn5HI-ByduwUw98bdTCXAzJK-9G9Lsw3P387YyuYlO2kx92LhiW0E3NVsob-knw9V8ndwUmFGPTpFlWOVZ8HPYPeyimwlaKFjJZ8tV9-p9S8mKTk_HJ15xGjZNj36Ev-Q9kO9IeRMlOu0gnA6SV5eLLpk7W0ZijcIqLcwn10LAz7gyGTEAtGny4TTfdB3uuQJgdi3-wauwOcYdRQ-8DHa-Dr51gXzEzF4O7S6hhPCFsKdfXbRb566q8SZMFQjLBwiQxb7uHC1ozpzXkdBtIUQhDuF1CJFocGiw	AQB6FiL3tOSTh2iHgEVxz3OdmkR0tn4QsThRlEsXdQmpKx3itz3ekuVDmJDSHeJ0Dcz5RWmHHrpP8LLYVYmA3HZezdT5rsl6IlqHXIdByWrGOqgENZVLi6-fqXAQsQol5WA	2025-08-15 22:35:53.86437	5	2025-08-08 03:32:52.658946	t	\N
17	pklaft24	IdleChipmunk	Phil Klafta	\N	BQChqHSXvBexlBYfUwv4bnQonO8YvibSTffLwtK1ODXhrbObDDReCfr00eSzPBUzVJJPZubT1bWzO4QA0EWvp2CkMKh_6jovseQlD03533TwH8FE05um5xAqR_yrv6IemQxl3DF5WsRMBqEkc97sBpAfbsd4BpwPggA2IIC1mYc1CHRC49xJWi6QqO7DA9gYC_BkZrTrLoRqup5bJgYXXgI10FR2A6gNg7ldtiCzVdLuJuzZYtx0Kr8LN4iO3ZiF3V8Muy3wvpIGnpk12s-vDarIcIRuT6g	AQARlktmuqkxQYsHupwo9OoVL5Xwcmk_Yhz3hwZGrAWbwMaod8rLyFQ2ioOBpoRCoQWdG3FX0FNJ1GDJaf0q986CyR6jWkQFF4NxX4NMiYJ8Sbopp7oWYi-bwDR3SQ2SLlI	2025-08-15 21:29:01.257708	5	2025-08-15 20:29:01.386765	f	\N
18	j1vssqzd531sdz3l71vlnb2cy	Brando.t10	Brando	\N	BQDZ4q2i-LcvygC9mTFmHhWbEWLztQLPNY3YOxBDZJV19GMfvkWaKr8gDyUfw8lg-mR_h2RWvr9lrxk3KzVzyxYqDFvLuDh56oy7Qc58HVhZzBiQmx0FlxIrAdKqlVX-SYFRg82tn5plY1hwdKIb7Vv5_deXoJ7p40XPlD-nP7hrxUqyZRVLpQglyIy6TMcAclTJ6O-54cYDxUR9BbUBFgj5oZ1VIp_XZXW2Gv5G3mR-jcXhAqVm4fwbq21mKiXrSnkVpeYfqE-uWcl0QfEaOEQZyFVjpfvprS6SpX-tYkuneeiuLsU73g	AQDq1QwHbBvG6xT8mcv_IgQ58sy8MEjoFy8toewS3N50-Nj9k8nAMTjzVcfc2_TZgaffDRDaNDDES2_pBkQa-Cet-Pb2s4AtSrfx5sj4V-0o60r7e_lrbxk-0nUZ_swPD_M	2025-08-15 21:40:46.359768	5	2025-08-15 20:40:46.505082	f	\N
\.


--
-- Data for Name: vibe_scores; Type: TABLE DATA; Schema: public; Owner: vibedrop_prod_db_user
--

COPY public.vibe_scores (id, user1_id, user2_id, vibe_index, last_updated) FROM stdin;
\.


--
-- Name: circle_membership_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.circle_membership_id_seq', 22, true);


--
-- Name: drop_creds_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.drop_creds_id_seq', 1, false);


--
-- Name: song_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.song_feedback_id_seq', 11, true);


--
-- Name: sound_circle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.sound_circle_id_seq', 5, true);


--
-- Name: submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.submission_id_seq', 31, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.user_id_seq', 18, true);


--
-- Name: vibe_score_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vibedrop_prod_db_user
--

SELECT pg_catalog.setval('public.vibe_score_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: circle_memberships circle_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_pkey PRIMARY KEY (id);


--
-- Name: drop_creds pk_drop_creds; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.drop_creds
    ADD CONSTRAINT pk_drop_creds PRIMARY KEY (id);


--
-- Name: song_feedback pk_song_feedback; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT pk_song_feedback PRIMARY KEY (id);


--
-- Name: sound_circles sound_circle_pkey; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_pkey PRIMARY KEY (id);


--
-- Name: submissions submission_pkey; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_pkey PRIMARY KEY (id);


--
-- Name: circle_memberships unique_membership; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT unique_membership UNIQUE (user_id, circle_id);


--
-- Name: song_feedback unique_user_song_feedback; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT unique_user_song_feedback UNIQUE (user_id, song_id);


--
-- Name: sound_circles uq_sound_circles__circle_name; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT uq_sound_circles__circle_name UNIQUE (circle_name);


--
-- Name: sound_circles uq_sound_circles__invite_code; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT uq_sound_circles__invite_code UNIQUE (invite_code);


--
-- Name: users uq_users__spotify_id; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users__spotify_id UNIQUE (spotify_id);


--
-- Name: users uq_users__vibedrop_username; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users__vibedrop_username UNIQUE (vibedrop_username);


--
-- Name: users user_pkey; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: vibe_scores vibe_score_pkey; Type: CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_pkey PRIMARY KEY (id);


--
-- Name: ix_drop_creds_user_computed_at; Type: INDEX; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE INDEX ix_drop_creds_user_computed_at ON public.drop_creds USING btree (user_id, computed_at);


--
-- Name: ix_drop_creds_user_id; Type: INDEX; Schema: public; Owner: vibedrop_prod_db_user
--

CREATE INDEX ix_drop_creds_user_id ON public.drop_creds USING btree (user_id);


--
-- Name: circle_memberships circle_membership_circle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_circle_id_fkey FOREIGN KEY (circle_id) REFERENCES public.sound_circles(id);


--
-- Name: circle_memberships circle_membership_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: drop_creds fk_drop_creds__user_id__users; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.drop_creds
    ADD CONSTRAINT fk_drop_creds__user_id__users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: song_feedback fk_song_feedback__song_id__submission; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT fk_song_feedback__song_id__submission FOREIGN KEY (song_id) REFERENCES public.submissions(id);


--
-- Name: song_feedback fk_song_feedback__user_id__user; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT fk_song_feedback__user_id__user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sound_circles sound_circle_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: submissions submission_circle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_circle_id_fkey FOREIGN KEY (circle_id) REFERENCES public.sound_circles(id);


--
-- Name: submissions submission_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: vibe_scores vibe_score_user1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_user1_id_fkey FOREIGN KEY (user1_id) REFERENCES public.users(id);


--
-- Name: vibe_scores vibe_score_user2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: vibedrop_prod_db_user
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_user2_id_fkey FOREIGN KEY (user2_id) REFERENCES public.users(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO vibedrop_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO vibedrop_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO vibedrop_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO vibedrop_prod_db_user;


--
-- PostgreSQL database dump complete
--


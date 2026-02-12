--
-- PostgreSQL database dump
--

\restrict lJ6mVLboGniTY8F2ASJnv7egkqXhNu4SqbFwWIgzmbYlHc0yCcMfNDPpjbHijAG

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: action_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.action_type AS ENUM (
    'Call',
    'Email',
    'SMS',
    'Other'
);


--
-- Name: debt_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.debt_status AS ENUM (
    'New',
    'Plan',
    'Paid',
    'Closed',
    'Payment Plan'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: campaign_recipients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campaign_recipients (
    id integer NOT NULL,
    campaign_id integer,
    debt_id integer,
    debtor_id uuid,
    email_to character varying(255) NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    sendgrid_message_id character varying(255),
    error_message text,
    sent_at timestamp with time zone,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: campaign_recipients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.campaign_recipients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: campaign_recipients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.campaign_recipients_id_seq OWNED BY public.campaign_recipients.id;


--
-- Name: campaigns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campaigns (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    subject character varying(255) NOT NULL,
    html_content text,
    template_id character varying(255),
    filters jsonb,
    status character varying(50) DEFAULT 'draft'::character varying,
    total_recipients integer DEFAULT 0,
    sent_count integer DEFAULT 0,
    failed_count integer DEFAULT 0,
    sent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: campaigns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.campaigns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: campaigns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.campaigns_id_seq OWNED BY public.campaigns.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    sftp_folder_path character varying(512),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: debtors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.debtors (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    ssn_hash character varying(255) NOT NULL,
    first_name character varying(255) NOT NULL,
    last_name character varying(255) NOT NULL,
    dob date,
    address_1 character varying(255),
    address_2 character varying(255),
    city character varying(100),
    state character varying(2),
    zip_code character varying(20),
    phone character varying(50),
    mobile_consent boolean DEFAULT false,
    email character varying(255),
    do_not_contact boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    email_bounce_status character varying(50),
    email_last_bounced_at timestamp with time zone,
    email_unsubscribed boolean DEFAULT false,
    email_unsubscribed_at timestamp with time zone
);


--
-- Name: debts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.debts (
    id integer NOT NULL,
    debtor_id uuid,
    portfolio_id integer,
    client_reference_number character varying(100),
    original_account_number character varying(100) NOT NULL,
    original_creditor character varying(255),
    date_opened date,
    charge_off_date date,
    principal_balance numeric(12,2),
    fees_costs numeric(12,2),
    amount_due numeric(12,2) NOT NULL,
    last_payment_date date,
    last_payment_amount numeric(12,2),
    status public.debt_status DEFAULT 'New'::public.debt_status,
    date_assigned timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    total_paid_amount numeric(15,2) DEFAULT 0.00,
    last_payment_id integer,
    last_payment_reference character varying(255),
    last_payment_method character varying(50),
    face_value numeric(12,2)
);


--
-- Name: debts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.debts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: debts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.debts_id_seq OWNED BY public.debts.id;


--
-- Name: email_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_logs (
    id integer NOT NULL,
    debt_id integer,
    debtor_id uuid,
    email_to character varying(255) NOT NULL,
    email_from character varying(255) NOT NULL,
    subject character varying(255),
    template_id character varying(255),
    sendgrid_message_id character varying(255),
    status character varying(50) NOT NULL,
    error_message text,
    delivered_at timestamp with time zone,
    opened_at timestamp with time zone,
    clicked_at timestamp with time zone,
    bounced_at timestamp with time zone,
    bounce_reason text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: email_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.email_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: email_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.email_logs_id_seq OWNED BY public.email_logs.id;


--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_templates (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    template_id character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: email_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.email_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: email_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.email_templates_id_seq OWNED BY public.email_templates.id;


--
-- Name: interaction_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.interaction_logs (
    id integer NOT NULL,
    debt_id integer,
    agent_id character varying(100),
    action_type public.action_type NOT NULL,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    notes text
);


--
-- Name: interaction_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.interaction_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: interaction_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.interaction_logs_id_seq OWNED BY public.interaction_logs.id;


--
-- Name: payment_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_plans (
    id integer NOT NULL,
    debt_id integer,
    total_settlement_amount numeric(15,2) NOT NULL,
    down_payment_amount numeric(15,2) DEFAULT 0.00,
    installment_count integer NOT NULL,
    frequency character varying(50) NOT NULL,
    start_date date NOT NULL,
    status character varying(50) DEFAULT 'active'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    card_token character varying(255),
    is_settlement boolean DEFAULT true
);


--
-- Name: payment_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_plans_id_seq OWNED BY public.payment_plans.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    debt_id integer,
    amount_paid numeric(12,2) NOT NULL,
    agency_portion numeric(12,2) NOT NULL,
    client_portion numeric(12,2) NOT NULL,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    transaction_reference character varying(255),
    scheduled_payment_id integer,
    payment_method character varying(50),
    status character varying(20) DEFAULT 'paid'::character varying,
    result_code character varying(10),
    result character varying(255),
    decline_reason character varying(50),
    error_message text
);


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: portfolios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolios (
    id integer NOT NULL,
    client_id integer,
    name character varying(255) NOT NULL,
    commission_percentage numeric(5,2) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT portfolios_commission_percentage_check CHECK (((commission_percentage >= (0)::numeric) AND (commission_percentage <= (100)::numeric)))
);


--
-- Name: portfolios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.portfolios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: portfolios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.portfolios_id_seq OWNED BY public.portfolios.id;


--
-- Name: scheduled_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scheduled_payments (
    id integer NOT NULL,
    plan_id integer,
    amount numeric(15,2) NOT NULL,
    due_date date NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    actual_payment_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp with time zone,
    transaction_reference character varying(255),
    payment_method character varying(50),
    attempt_count integer DEFAULT 0,
    next_attempt_at timestamp with time zone,
    last_attempt_at timestamp with time zone,
    last_gateway_trankey character varying(255),
    last_result_code character varying(10),
    last_result character varying(255),
    last_decline_reason character varying(50),
    last_error text
);


--
-- Name: scheduled_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scheduled_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scheduled_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scheduled_payments_id_seq OWNED BY public.scheduled_payments.id;


--
-- Name: campaign_recipients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_recipients ALTER COLUMN id SET DEFAULT nextval('public.campaign_recipients_id_seq'::regclass);


--
-- Name: campaigns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaigns ALTER COLUMN id SET DEFAULT nextval('public.campaigns_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Name: debts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debts ALTER COLUMN id SET DEFAULT nextval('public.debts_id_seq'::regclass);


--
-- Name: email_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_logs ALTER COLUMN id SET DEFAULT nextval('public.email_logs_id_seq'::regclass);


--
-- Name: email_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates ALTER COLUMN id SET DEFAULT nextval('public.email_templates_id_seq'::regclass);


--
-- Name: interaction_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interaction_logs ALTER COLUMN id SET DEFAULT nextval('public.interaction_logs_id_seq'::regclass);


--
-- Name: payment_plans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_plans ALTER COLUMN id SET DEFAULT nextval('public.payment_plans_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: portfolios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolios ALTER COLUMN id SET DEFAULT nextval('public.portfolios_id_seq'::regclass);


--
-- Name: scheduled_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_payments ALTER COLUMN id SET DEFAULT nextval('public.scheduled_payments_id_seq'::regclass);


--
-- Name: campaign_recipients campaign_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT campaign_recipients_pkey PRIMARY KEY (id);


--
-- Name: campaigns campaigns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: debtors debtors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debtors
    ADD CONSTRAINT debtors_pkey PRIMARY KEY (id);


--
-- Name: debtors debtors_ssn_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debtors
    ADD CONSTRAINT debtors_ssn_hash_key UNIQUE (ssn_hash);


--
-- Name: debts debts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debts
    ADD CONSTRAINT debts_pkey PRIMARY KEY (id);


--
-- Name: email_logs email_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_pkey PRIMARY KEY (id);


--
-- Name: email_templates email_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);


--
-- Name: interaction_logs interaction_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interaction_logs
    ADD CONSTRAINT interaction_logs_pkey PRIMARY KEY (id);


--
-- Name: payment_plans payment_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_plans
    ADD CONSTRAINT payment_plans_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: portfolios portfolios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_pkey PRIMARY KEY (id);


--
-- Name: scheduled_payments scheduled_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_payments
    ADD CONSTRAINT scheduled_payments_pkey PRIMARY KEY (id);


--
-- Name: idx_campaign_recipients_campaign_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_campaign_recipients_campaign_id ON public.campaign_recipients USING btree (campaign_id);


--
-- Name: idx_campaign_recipients_debt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_campaign_recipients_debt_id ON public.campaign_recipients USING btree (debt_id);


--
-- Name: idx_email_logs_debt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_email_logs_debt_id ON public.email_logs USING btree (debt_id);


--
-- Name: idx_email_logs_debtor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_email_logs_debtor_id ON public.email_logs USING btree (debtor_id);


--
-- Name: idx_email_logs_sendgrid_message_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_email_logs_sendgrid_message_id ON public.email_logs USING btree (sendgrid_message_id);


--
-- Name: idx_interaction_logs_debt_id_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interaction_logs_debt_id_timestamp ON public.interaction_logs USING btree (debt_id, "timestamp");


--
-- Name: campaign_recipients campaign_recipients_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT campaign_recipients_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.campaigns(id) ON DELETE CASCADE;


--
-- Name: campaign_recipients campaign_recipients_debt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT campaign_recipients_debt_id_fkey FOREIGN KEY (debt_id) REFERENCES public.debts(id);


--
-- Name: campaign_recipients campaign_recipients_debtor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT campaign_recipients_debtor_id_fkey FOREIGN KEY (debtor_id) REFERENCES public.debtors(id);


--
-- Name: debts debts_debtor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debts
    ADD CONSTRAINT debts_debtor_id_fkey FOREIGN KEY (debtor_id) REFERENCES public.debtors(id);


--
-- Name: debts debts_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debts
    ADD CONSTRAINT debts_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id);


--
-- Name: email_logs email_logs_debt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_debt_id_fkey FOREIGN KEY (debt_id) REFERENCES public.debts(id);


--
-- Name: email_logs email_logs_debtor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_debtor_id_fkey FOREIGN KEY (debtor_id) REFERENCES public.debtors(id);


--
-- Name: interaction_logs interaction_logs_debt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interaction_logs
    ADD CONSTRAINT interaction_logs_debt_id_fkey FOREIGN KEY (debt_id) REFERENCES public.debts(id);


--
-- Name: payment_plans payment_plans_debt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_plans
    ADD CONSTRAINT payment_plans_debt_id_fkey FOREIGN KEY (debt_id) REFERENCES public.debts(id);


--
-- Name: payments payments_debt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_debt_id_fkey FOREIGN KEY (debt_id) REFERENCES public.debts(id);


--
-- Name: portfolios portfolios_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id);


--
-- Name: scheduled_payments scheduled_payments_actual_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_payments
    ADD CONSTRAINT scheduled_payments_actual_payment_id_fkey FOREIGN KEY (actual_payment_id) REFERENCES public.payments(id);


--
-- Name: scheduled_payments scheduled_payments_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_payments
    ADD CONSTRAINT scheduled_payments_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.payment_plans(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict lJ6mVLboGniTY8F2ASJnv7egkqXhNu4SqbFwWIgzmbYlHc0yCcMfNDPpjbHijAG


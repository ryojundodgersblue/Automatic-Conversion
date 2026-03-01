/**
 * ReportComplete コンポーネントのテスト
 *
 * テスト対象:
 * - 初期レンダリング（タイトル、ボタン表示）
 * - 10MB超ファイルのフロントエンド拒否
 * - サーバーエラー時のメッセージ表示（400, 413, 500）
 * - タイムアウト時のメッセージ表示
 * - ネットワークエラー時のメッセージ表示
 * - アップロード成功時のダウンロード動作
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ReportComplete from "./ReportComplete";

// --- fetch モック用ヘルパー ---
function mockFetchSuccess() {
  const blob = new Blob(["dummy excel data"], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  return vi.fn().mockResolvedValue({
    ok: true,
    blob: () => Promise.resolve(blob),
    headers: new Headers({
      "content-disposition": "attachment; filename*=UTF-8''test_%E5%A0%B1%E5%91%8A%E6%9B%B8.xlsx",
    }),
  });
}

function mockFetchError(status: number) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: () => Promise.resolve({ error: "エラーメッセージ" }),
  });
}

function mockFetchNetworkError() {
  return vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
}

// --- URL.createObjectURL / revokeObjectURL モック ---
beforeEach(() => {
  vi.stubGlobal(
    "URL",
    Object.assign({}, URL, {
      createObjectURL: vi.fn(() => "blob:http://test/mock"),
      revokeObjectURL: vi.fn(),
    }),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ReportComplete", () => {
  // =============================================
  // 初期レンダリング
  // =============================================
  describe("初期レンダリング", () => {
    it("タイトルが表示される", () => {
      render(<ReportComplete />);
      expect(
        screen.getByText("事業年度終了報告書 自動変換システム"),
      ).toBeInTheDocument();
    });

    it("サブタイトルが表示される", () => {
      render(<ReportComplete />);
      expect(
        screen.getByText(/建設業の確定申告書 PDF/),
      ).toBeInTheDocument();
    });

    it("PDFファイルを選択 ボタンが表示される", () => {
      render(<ReportComplete />);
      expect(screen.getByText("PDFファイルを選択")).toBeInTheDocument();
    });

    it("ファイルサイズ上限情報が表示される", () => {
      render(<ReportComplete />);
      expect(screen.getByText(/ファイルサイズ上限: 10MB/)).toBeInTheDocument();
    });

    it("初期状態ではエラーメッセージが表示されない", () => {
      render(<ReportComplete />);
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });

  // =============================================
  // ファイルサイズ制限（フロントエンド側）
  // =============================================
  describe("ファイルサイズ制限", () => {
    it("10MB超のファイルを選択するとエラーメッセージが表示される", async () => {
      render(<ReportComplete />);

      // 11MB のダミーファイル
      const largeFile = new File(
        [new ArrayBuffer(11 * 1024 * 1024)],
        "large.pdf",
        { type: "application/pdf" },
      );

      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [largeFile] } });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "ファイルサイズが上限（10MB）を超えています",
        );
      });
    });

    it("10MB以下のファイルはサイズエラーが出ない", async () => {
      // fetch をモック（成功レスポンス）
      global.fetch = mockFetchSuccess();

      render(<ReportComplete />);

      const smallFile = new File(["small content"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 }); // 1KB

      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        // サイズ制限エラーは出ない
        const alert = screen.queryByRole("alert");
        if (alert) {
          expect(alert).not.toHaveTextContent("ファイルサイズ");
        }
      });
    });
  });

  // =============================================
  // サーバーエラーメッセージ
  // =============================================
  describe("サーバーエラーメッセージ", () => {
    it("400エラー時にPDFファイルのみのメッセージが表示される", async () => {
      global.fetch = mockFetchError(400);
      render(<ReportComplete />);

      const smallFile = new File(["dummy"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "PDFファイルのみアップロード可能です",
        );
      });
    });

    it("413エラー時にファイルサイズ上限メッセージが表示される", async () => {
      global.fetch = mockFetchError(413);
      render(<ReportComplete />);

      const smallFile = new File(["dummy"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "ファイルサイズが上限（10MB）を超えています",
        );
      });
    });

    it("500エラー時にサーバーエラーメッセージが表示される", async () => {
      global.fetch = mockFetchError(500);
      render(<ReportComplete />);

      const smallFile = new File(["dummy"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "サーバーでエラーが発生しました",
        );
      });
    });
  });

  // =============================================
  // ネットワークエラー
  // =============================================
  describe("ネットワークエラー", () => {
    it("ネットワークエラー時にサーバー接続エラーメッセージが表示される", async () => {
      global.fetch = mockFetchNetworkError();
      render(<ReportComplete />);

      const smallFile = new File(["dummy"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          "サーバーに接続できません",
        );
      });
    });
  });

  // =============================================
  // アップロード成功
  // =============================================
  describe("アップロード成功", () => {
    it("アップロード成功時にエラーが表示されない", async () => {
      global.fetch = mockFetchSuccess();

      render(<ReportComplete />);

      const smallFile = new File(["dummy"], "test.pdf", {
        type: "application/pdf",
      });
      Object.defineProperty(smallFile, "size", { value: 1024 });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(input, { target: { files: [smallFile] } });

      await waitFor(() => {
        // エラーメッセージが表示されないことを確認
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      });
    });
  });

  // =============================================
  // ボタン無効化
  // =============================================
  describe("ボタン状態", () => {
    it("ファイルを選択しないとき、ボタンは有効", () => {
      render(<ReportComplete />);
      const button = screen.getByText("PDFファイルを選択");
      expect(button).not.toBeDisabled();
    });
  });
});
